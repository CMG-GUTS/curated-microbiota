import gzip
import hashlib
import io
import sys
import tarfile
from types import SimpleNamespace

from curated_microbiota import MLLABIOME_BENCHMARK, MLLABIOME_NCV, __data_release__, collections
from curated_microbiota._fetch import _base


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as bundle:
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mtime = 0
                bundle.addfile(info, io.BytesIO(data))
    return stream.getvalue()


def test_collections():
    assert collections.brown_mdd.targets == ("mdd", "promis_depression")
    assert collections.brown_mdd.target("mdd").problem_type == "binary_classification"
    assert collections.brown_mdd.target("promis_depression").problem_type == "regression"
    assert collections.brown_mdd.target("mdd").column == "target_mdd"
    assert collections.brown_mdd.target("promis_depression").column == "target_depression_severity"
    assert collections.prjna1190316.benchmark_targets == ("mdd",)
    assert collections.healthy_colombia.benchmark_targets == ("zung_depression",)
    assert collections.healthy_colombia.target().problem_type == "regression"
    assert collections.healthy_colombia.splits().design.repeats == 3
    assert collections.healthy_colombia.accession == "PRJNA1000574"
    assert collections.healthy_colombia.sequencing.region == "V3-V4"
    assert MLLABIOME_BENCHMARK.id == "mllabiome-benchmark-v1"
    assert MLLABIOME_NCV.outer_folds == 5
    assert MLLABIOME_NCV.inner_folds == 3
    assert MLLABIOME_NCV.repeats == 3
    lampp = {study.name for study in collections.available(role="benchmark")}
    assert lampp == {
        "healthy_colombia",
        "metaibs_ibs",
        "ibd_multiclass",
        "prime_ptsd",
        "lampp_scz",
        "lampp_crc",
        "lampp_ghs",
        "lampp_ibd",
        "lampp_dm7",
        "lampp_dm90",
    }
    assert collections.metaibs_ibs.splits().protocol == "lodo"
    assert collections.ibd_multiclass.target().problem_type == "multiclass_classification"
    assert collections.ibd_multiclass.target().class_labels == ("Control", "CD", "UC")
    assert collections.ibd_multiclass.splits().protocol == "lodo"
    assert collections.ibd_multiclass.splits().design.outer_folds == 4
    assert collections.ibd_multiclass.splits().design.inner_folds == 3
    assert collections.ibd_multiclass.splits().design.inner_grouping == "outer_group"
    assert collections.available(problem_type="multiclass_classification") == (collections.ibd_multiclass,)
    assert collections.metaibs_ibs.splits().design.outer_folds == 6
    assert collections.metaibs_ibs.splits().design.inner_grouping == "outer_group"
    assert collections.metaibs_ibs.source is not None
    assert collections.metaibs_ibs.source.name == "MetaIBS"
    assert collections.prime_ptsd.splits().protocol == "repeated_nested_cv"
    assert collections.prime_ptsd.splits().design.repeats == 3
    assert collections.prime_ptsd.source is not None
    assert collections.prime_ptsd.source.name == "PRIME"
    assert collections.prime_ptsd.samples == 169
    assert collections.prime_ptsd.target().problem_type == "binary_classification"
    assert collections.available(problem_type="regression") == (collections.brown_mdd, collections.healthy_colombia)
    assert collections.lampp_scz.splits().protocol == "repeated_nested_cv"
    assert collections.lampp_crc.splits().protocol == "lodo"
    assert collections.lampp_ghs.splits().design.inner_grouping == "outer_group"
    assert collections.lampp_ibd.splits().design.inner_grouping == "subject"
    assert collections.lampp_dm7.splits().design.inner_grouping == "subject"
    assert collections.lampp_dm90.splits().design.inner_grouping == "subject"
    assert collections.lampp_crc.external_test is not None
    assert collections.lampp_crc.external_test.labels_available is False
    assert collections.lampp_crc.source is not None
    assert collections.lampp_crc.source.name == "LAMPP"


def test_fetch(tmp_path, monkeypatch):
    study = collections.brown_mdd
    payloads = {}
    for file in study._files:
        if file.name == "counts.tsv":
            payloads[file.name] = b"feature_id\ts1\nx\t1\n"
        elif file.name == "metadata.tsv":
            payloads[file.name] = b"sample_id\ttarget_mdd\ns1\t1\n"
        elif file.name == "feature_metadata.tsv":
            payloads[file.name] = b"feature_id\nx\n"
        elif file.name == "qc.tsv":
            payloads[file.name] = b"sample_id\tqc_pass\ns1\t1\n"
        elif file.name == "provenance.yaml":
            payloads[file.name] = b"study: test\n"
        else:
            payloads[file.name] = b"schema_version\tsample_id\n3\ts1\n"
    archive = _archive(payloads)
    source = tmp_path / "source"
    source.mkdir()
    asset = source / study._asset
    asset.write_bytes(archive)
    files = tuple(type(file)(file.name, _sha(payloads[file.name])) for file in study._files)
    local = type(study)(
        name=study.name,
        title=study.title,
        version=study.version,
        accession=study.accession,
        condition=study.condition,
        assay=study.assay,
        role=study.role,
        status=study.status,
        samples=study.samples,
        features=study.features,
        population=study.population,
        country=study.country,
        sample_type=study.sample_type,
        sequencing=study.sequencing,
        source=study.source,
        confounders=study.confounders,
        _asset=asset.name,
        _asset_sha256=_sha(archive),
        _files=files,
        _targets=study._targets,
        _splits=study._splits,
        _external=study._external,
        _default=study._default,
        _abundance=study._abundance,
        _metadata=study._metadata,
        _feature_metadata=study._feature_metadata,
        _qc=study._qc,
        _provenance=study._provenance,
        _format=study._format,
        _sample_id=study._sample_id,
        _subject=study._subject,
        _group=study._group,
        _stratify=study._stratify,
    )
    monkeypatch.setenv("CURATED_MICROBIOTA_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("CURATED_MICROBIOTA_RELEASE_URL", source.as_uri())
    assert local.counts.read_bytes() == payloads["counts.tsv"]
    assert local.splits("mdd").path.read_bytes() == payloads["splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv"]
    assert local.cached


def test_mllabiome(tmp_path, monkeypatch):
    study = collections.lampp_ibd
    profiles = tmp_path / "profiles.tsv"
    metadata = tmp_path / "metadata.tsv"
    test_profiles = tmp_path / "test_profiles.tsv"
    test_metadata = tmp_path / "test_metadata.tsv"
    splits = tmp_path / "cv_splits.tsv"
    profiles.write_text("clade_name\ts1\nx\t1\n")
    metadata.write_text("sampleId\tlabel\tsubject_id\tstudy_id\ns1\t1\tu1\ta\n")
    test_profiles.write_text("clade_name\tt1\nx\t1\n")
    test_metadata.write_text("sampleId\nt1\n")
    splits.write_text("schema_version\tsample_id\n3\ts1\n")
    paths = {
        "profiles.tsv": profiles,
        "metadata.tsv": metadata,
        "test_profiles.tsv": test_profiles,
        "test_metadata.tsv": test_metadata,
        "splits/ibd/mllabiome-benchmark-v1/cv_splits.tsv": splits,
    }
    monkeypatch.setattr(type(study), "_file", lambda self, name: paths.get(name, tmp_path / name))
    module = SimpleNamespace(
        Data=lambda **values: SimpleNamespace(**values),
        Evaluation=lambda **values: SimpleNamespace(**values),
        Inference=lambda **values: SimpleNamespace(**values),
    )
    monkeypatch.setitem(sys.modules, "mllabiome", module)
    data = study.mllabiome()
    evaluation = study.splits().mllabiome(optimize_metric="log_loss")
    inference = study.external_test.inference()
    assert data.target_col == "label"
    assert data.format == "metaphlan_tsv"
    assert data.group_col == "study_id"
    assert data.subject_id_col == "subject_id"
    assert evaluation.protocol == "lodo"
    assert evaluation.outer_folds == 2
    assert evaluation.inner_folds == 3
    assert evaluation.repeats == 1
    assert evaluation.inner_grouping == "subject"
    assert evaluation.benchmark_id == "mllabiome-benchmark-v1"
    assert evaluation.split_manifest == str(splits)
    assert inference.abundance_path == test_profiles
    assert inference.metadata_path == test_metadata
    assert inference.sample_id_col == "sampleId"


def test_lampp_submission(tmp_path, monkeypatch):
    study = collections.lampp_crc
    test_metadata = tmp_path / "test_metadata.tsv"
    test_metadata.write_text("sampleId\nt2\nt1\n")
    monkeypatch.setattr(
        type(study),
        "_file",
        lambda self, name: test_metadata if name == "test_metadata.tsv" else tmp_path / name,
    )
    predictions = tmp_path / "predictions.tsv"
    predictions.write_text(
        "sample_id\tmpma_b_predicted_class\tmpma_b_probability_0\tmpma_b_probability_1\n"
        "t1\t1\t0.2\t0.8\n"
        "t2\t0\t0.7\t0.3\n"
    )
    output = study.external_test.submission(predictions, strategy="mpma_b")
    assert output.read_text() == "sample_id,prediction\nt2,0.3\nt1,0.8\n"


def test_prime_ptsd_mllabiome(tmp_path, monkeypatch):
    study = collections.prime_ptsd
    profiles = tmp_path / "profiles.tsv"
    metadata = tmp_path / "metadata.tsv"
    splits = tmp_path / "cv_splits.tsv"
    profiles.write_text("clade_name\ts1\nx\t1\n")
    metadata.write_text("sampleId\tlabel\tsubject_id\ttime_point\ns1\t1\tu1\tBL\n")
    splits.write_text("schema_version\tsample_id\n3\ts1\n")
    paths = {
        "profiles.tsv": profiles,
        "metadata.tsv": metadata,
        "splits/intervention/mllabiome-benchmark-v1/cv_splits.tsv": splits,
    }
    monkeypatch.setattr(type(study), "_file", lambda self, name: paths.get(name, tmp_path / name))
    module = SimpleNamespace(
        Data=lambda **values: SimpleNamespace(**values),
        Evaluation=lambda **values: SimpleNamespace(**values),
    )
    monkeypatch.setitem(sys.modules, "mllabiome", module)
    data = study.mllabiome()
    evaluation = study.splits().mllabiome()
    assert data.group_col == "subject_id"
    assert data.subject_id_col == "subject_id"
    assert data.stratify_col == "time_point"
    assert data.positive_class == 1
    assert evaluation.protocol == "repeated_nested_cv"
    assert evaluation.outer_folds == 5
    assert evaluation.inner_folds == 3
    assert evaluation.repeats == 3


def test_packaged_release_manifest():
    assert __data_release__ == "data-v0.1.3"
    assert _base().endswith("/data-v0.1.3")
    assert collections.brown_mdd.version == "0.1.1"
    assert collections.brown_mdd._asset == "brown_mdd-0.1.1.tar.gz"
    assert collections.metaibs_ibs.version == "0.1.1"
    assert collections.prime_ptsd.version == "0.1.1"
    assert collections.healthy_colombia.version == "0.1.3"
    assert collections.healthy_colombia._asset == "healthy_colombia-0.1.3.tar.gz"
    assert collections.ibd_multiclass.version == "0.1.0"
    assert collections.ibd_multiclass._asset == "ibd_multiclass-0.1.0.tar.gz"
