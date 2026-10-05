from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ._errors import UnavailableError
from ._fetch import cached as _cached
from ._fetch import fetch as _fetch

Task = Literal["classification", "regression"]
ProblemType = Literal["binary_classification", "multiclass_classification", "regression"]


@dataclass(frozen=True, slots=True)
class Source:
    name: str
    title: str = ""
    doi: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class Sequencing:
    assay: str
    region: str | None = None
    forward_primer: str | None = None
    reverse_primer: str | None = None
    platform: str | None = None
    instrument: str | None = None
    layout: str | None = None
    read_length: str | None = None


@dataclass(frozen=True, slots=True)
class Target:
    name: str
    column: str
    task: Task
    problem_type: ProblemType
    positive_class: int | str | None = None
    class_labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Benchmark:
    name: str
    version: int

    @property
    def id(self) -> str:
        return f"{self.name}-v{self.version}"


@dataclass(frozen=True, slots=True)
class EvaluationDesign:
    protocol: str
    outer_folds: int
    inner_folds: int
    repeats: int
    random_state: int = 42
    inner_grouping: str = "auto"


MLLABIOME_BENCHMARK = Benchmark(name="mllabiome-benchmark", version=2)
MLLABIOME_NCV = EvaluationDesign(
    protocol="repeated_nested_cv",
    outer_folds=5,
    inner_folds=3,
    repeats=2,
    random_state=42,
    inner_grouping="auto",
)


@dataclass(frozen=True, slots=True)
class _File:
    name: str
    sha256: str


@dataclass(frozen=True, slots=True)
class _Target:
    name: str
    column: str
    task: Task
    positive: int | str | None = None
    classes: tuple[str, ...] = ()
    labels: tuple[tuple[int | str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class _Split:
    target: str
    benchmark: Benchmark
    design: EvaluationDesign
    file: str


@dataclass(frozen=True, slots=True)
class _External:
    abundance: str
    metadata: str | None = None
    labels_available: bool = False
    evaluator: str | None = None


@dataclass(frozen=True, slots=True)
class SplitSet:
    study: Study
    target: str
    benchmark: Benchmark
    design: EvaluationDesign
    file: str

    @property
    def path(self) -> Path:
        return self.study._file(self.file)

    @property
    def protocol(self) -> str:
        return self.design.protocol

    def mllabiome(self, **values: Any) -> Any:
        try:
            import mllabiome
        except ModuleNotFoundError as exc:
            if exc.name == "mllabiome":
                raise ImportError("Install mllabiome to use this adapter") from exc
            raise
        settings = {
            "protocol": self.design.protocol,
            "outer_folds": self.design.outer_folds,
            "inner_folds": self.design.inner_folds,
            "repeats": self.design.repeats,
            "random_state": self.design.random_state,
            "benchmark_id": self.benchmark.id,
            "inner_grouping": self.design.inner_grouping,
            "split_manifest": str(self.path),
        }
        settings.update(values)
        return mllabiome.Evaluation(**settings)


@dataclass(frozen=True, slots=True)
class ExternalSet:
    study: Study
    abundance_file: str
    metadata_file: str | None
    labels_available: bool
    evaluator: str | None

    @property
    def abundance(self) -> Path:
        return self.study._file(self.abundance_file)

    @property
    def metadata(self) -> Path | None:
        return None if self.metadata_file is None else self.study._file(self.metadata_file)

    def inference(self, targets: tuple[str, ...] = ("mpma_b", "mpma_e"), **values: Any) -> Any:
        try:
            import mllabiome
        except ModuleNotFoundError as exc:
            if exc.name == "mllabiome":
                raise ImportError("Install mllabiome to use this adapter") from exc
            raise
        settings = {
            "abundance_path": self.abundance,
            "metadata_path": self.metadata,
            "format": self.study._format,
            "sample_id_col": self.study._sample_id,
            "targets": targets,
        }
        settings.update(values)
        return mllabiome.Inference(**settings)

    def mllabiome(self, targets: tuple[str, ...] = ("mpma_b", "mpma_e"), **values: Any) -> Any:
        return self.inference(targets=targets, **values)

    def submission(
        self,
        predictions: str | Path,
        strategy: str = "mpma_b",
        output: str | Path | None = None,
    ) -> Path:
        selected = self.study._target(None)
        if selected.task != "classification":
            raise ValueError("External submission export requires a classification target")
        if selected.positive is None:
            raise ValueError("External submission export requires a positive class")
        prefix = strategy.casefold().replace("-", "_")
        token = re.sub(r"[^0-9A-Za-z]+", "_", str(selected.positive)).strip("_") or "class"
        probability_column = f"{prefix}_probability_{token}"
        source = Path(predictions)
        with source.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = tuple(reader.fieldnames or ())
            if "sample_id" not in fields or probability_column not in fields:
                raise ValueError(
                    f"Inference predictions must contain 'sample_id' and {probability_column!r}"
                )
            values = {}
            for row in reader:
                sample_id = str(row["sample_id"])
                if sample_id in values:
                    raise ValueError(f"Duplicate inference sample_id: {sample_id}")
                probability = float(row[probability_column])
                if not math.isfinite(probability) or probability < 0.0 or probability > 1.0:
                    raise ValueError(f"Invalid probability for sample {sample_id}: {probability}")
                values[sample_id] = probability
        metadata = self.metadata
        if metadata is None:
            expected = tuple(values)
        else:
            with metadata.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                fields = tuple(reader.fieldnames or ())
                if self.study._sample_id not in fields:
                    raise ValueError(
                        f"External metadata must contain {self.study._sample_id!r}"
                    )
                expected = tuple(str(row[self.study._sample_id]) for row in reader)
        if len(expected) != len(set(expected)):
            raise ValueError("External metadata contains duplicate sample identifiers")
        if set(expected) != set(values):
            missing = sorted(set(expected) - set(values))
            extra = sorted(set(values) - set(expected))
            raise ValueError(
                f"Inference predictions do not match the external test set; missing={missing[:5]!r}, extra={extra[:5]!r}"
            )
        destination = (
            Path(output)
            if output is not None
            else source.with_name(f"{prefix}_lampp_predictions.csv")
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("sample_id", "prediction"))
            writer.writerows((sample_id, values[sample_id]) for sample_id in expected)
        temporary.replace(destination)
        return destination


@dataclass(frozen=True, slots=True)
class Study:
    name: str
    title: str
    version: str
    accession: str
    condition: str
    assay: str
    role: str
    status: str
    samples: int
    features: int
    population: str = ""
    country: str = ""
    sample_type: str = "stool"
    sequencing: Sequencing | None = None
    source: Source | None = None
    confounders: tuple[str, ...] = ()
    _asset: str = field(default="", repr=False)
    _asset_sha256: str = field(default="", repr=False)
    _files: tuple[_File, ...] = field(default=(), repr=False)
    _targets: tuple[_Target, ...] = field(default=(), repr=False)
    _splits: tuple[_Split, ...] = field(default=(), repr=False)
    _external: _External | None = field(default=None, repr=False)
    _default: str | None = field(default=None, repr=False)
    _abundance: str = field(default="counts.tsv", repr=False)
    _metadata: str = field(default="metadata.tsv", repr=False)
    _feature_metadata: str | None = field(default="feature_metadata.tsv", repr=False)
    _qc: str | None = field(default="qc.tsv", repr=False)
    _provenance: str | None = field(default="provenance.yaml", repr=False)
    _format: str = field(default="mllab", repr=False)
    _sample_id: str = field(default="sample_id", repr=False)
    _subject: str | None = field(default="subject_id", repr=False)
    _group: str | None = field(default=None, repr=False)
    _stratify: str | tuple[str, ...] | None = field(default=None, repr=False)
    _ready: bool = field(default=True, repr=False)

    @property
    def targets(self) -> tuple[str, ...]:
        return tuple(target.name for target in self._targets)

    @property
    def benchmark_targets(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(split.target for split in self._splits))

    def target(self, name: str | None = None) -> Target:
        selected = self._target(name)
        if selected.task == "regression":
            problem_type: ProblemType = "regression"
        elif len(selected.classes) == 2:
            problem_type = "binary_classification"
        else:
            problem_type = "multiclass_classification"
        return Target(
            name=selected.name,
            column=selected.column,
            task=selected.task,
            problem_type=problem_type,
            positive_class=selected.positive,
            class_labels=selected.classes,
        )

    @property
    def benchmark_target_info(self) -> tuple[Target, ...]:
        return tuple(self.target(name) for name in self.benchmark_targets)

    @property
    def cached(self) -> bool:
        return _cached(self.name, self.version, self._file_pairs())

    @property
    def path(self) -> Path:
        self._require_ready()
        return self._materialize()

    @property
    def abundance(self) -> Path:
        return self._file(self._abundance)

    @property
    def counts(self) -> Path:
        return self.abundance

    @property
    def metadata(self) -> Path:
        return self._file(self._metadata)

    @property
    def feature_metadata(self) -> Path | None:
        return None if self._feature_metadata is None else self._file(self._feature_metadata)

    @property
    def qc(self) -> Path | None:
        return None if self._qc is None else self._file(self._qc)

    @property
    def provenance(self) -> Path | None:
        return None if self._provenance is None else self._file(self._provenance)

    @property
    def external_test(self) -> ExternalSet | None:
        if self._external is None:
            return None
        return ExternalSet(
            self,
            self._external.abundance,
            self._external.metadata,
            self._external.labels_available,
            self._external.evaluator,
        )

    def fetch(self) -> Path:
        self._require_ready()
        return self._materialize()

    def splits(
        self,
        target: str | None = None,
        benchmark: str | Benchmark = MLLABIOME_BENCHMARK,
    ) -> SplitSet:
        selected = self._target(target)
        benchmark_id = benchmark.id if isinstance(benchmark, Benchmark) else str(benchmark)
        for split in self._splits:
            if split.target == selected.name and split.benchmark.id == benchmark_id:
                return SplitSet(
                    self,
                    selected.name,
                    split.benchmark,
                    split.design,
                    split.file,
                )
        available = tuple(
            split.benchmark.id for split in self._splits if split.target == selected.name
        )
        raise KeyError(
            f"No split set {benchmark_id!r} for target {selected.name!r}; available: {available!r}"
        )

    def mllabiome(self, target: str | None = None) -> Any:
        selected = self._target(target)
        try:
            import mllabiome
        except ModuleNotFoundError as exc:
            if exc.name == "mllabiome":
                raise ImportError("Install mllabiome to use this adapter") from exc
            raise
        return mllabiome.Data(
            abundance_path=self.abundance,
            metadata_path=self.metadata,
            format=self._format,
            sample_id_col=self._sample_id,
            target_col=selected.column,
            task=selected.task,
            group_col=self._group,
            subject_id_col=self._subject,
            stratify_col=self._stratify,
            label_map=dict(selected.labels) or None,
            class_labels=selected.classes or None,
            positive_class=selected.positive if selected.positive is not None else 1,
        )

    def _materialize(self) -> Path:
        return _fetch(self.name, self.version, self._asset, self._asset_sha256, self._file_pairs())

    def _file_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple((file.name, file.sha256) for file in self._files)

    def _file(self, name: str) -> Path:
        self._require_ready()
        if name not in {file.name for file in self._files}:
            raise AttributeError(name)
        return self._materialize() / name

    def _target(self, name: str | None) -> _Target:
        key = name or self._default
        if key is None:
            if len(self._targets) == 1:
                return self._targets[0]
            raise ValueError(f"Choose a target from {self.targets!r}")
        for target in self._targets:
            if target.name == key:
                return target
        raise KeyError(f"{key!r}; available targets: {self.targets!r}")

    def _require_ready(self) -> None:
        if not self._ready:
            raise UnavailableError(self.name)
