import argparse
import csv
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


def sha256_path(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest(payload):
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def snake(value):
    return "_".join("".join(char.lower() if char.isalnum() else " " for char in str(value)).split())


def split_signatures(sample_ids, y, groups, strata, subject_ids):
    records = sorted(
        (
            str(sample_ids[index]),
            int(y[index]),
            str(groups[index]),
            str(strata[index]),
            str(subject_ids[index]),
        )
        for index in range(len(sample_ids))
    )
    data_signature = digest({"task": "classification", "target_name": "label", "samples": records})
    plan_signature = digest(
        {
            "schema_version": 3,
            "protocol": "lodo",
            "outer_folds": 17,
            "inner_folds": 3,
            "repeats": 1,
            "random_state": 42,
            "group_col": "study_id",
            "stratify_col": None,
            "inner_grouping": "outer_group",
        }
    )
    return data_signature, plan_signature


def split_manifest(metadata):
    sample_ids = metadata["sampleId"].astype(str).tolist()
    subject_ids = metadata["subject_id"].astype(str).to_numpy(dtype=object)
    y = metadata["label"].astype(int).to_numpy()
    groups = metadata["study_id"].astype(str).to_numpy(dtype=object)
    strata = y.astype(str)
    data_signature, plan_signature = split_signatures(sample_ids, y, groups, strata, subject_ids)
    rows = []
    for outer_fold, outer_group in enumerate(pd.unique(groups)):
        test_idx = np.flatnonzero(groups == outer_group)
        train_idx = np.flatnonzero(groups != outer_group)
        split_key = f"lodo_{outer_fold}__{outer_group}"
        for role, indices in (("train", train_idx), ("test", test_idx)):
            for index in indices:
                rows.append(
                    {
                        "schema_version": 3,
                        "data_signature": data_signature,
                        "plan_signature": plan_signature,
                        "task": "classification",
                        "protocol": "lodo",
                        "stage": "outer",
                        "split_key": split_key,
                        "inner_key": "",
                        "repeat": 0,
                        "outer_fold": outer_fold,
                        "inner_fold": -1,
                        "outer_group": str(outer_group),
                        "role": role,
                        "sample_id": sample_ids[int(index)],
                        "sample_index": int(index),
                    }
                )
        local_y = y[train_idx]
        local_groups = groups[train_idx]
        splitter = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42 + outer_fold)
        for inner_fold, (inner_train, inner_validation) in enumerate(
            splitter.split(np.zeros(len(train_idx)), local_y.astype(str), local_groups)
        ):
            inner_key = f"{split_key}__i{inner_fold}"
            for role, local_indices in (("train", inner_train), ("validation", inner_validation)):
                global_indices = train_idx[np.asarray(local_indices, dtype=int)]
                for index in global_indices:
                    rows.append(
                        {
                            "schema_version": 3,
                            "data_signature": data_signature,
                            "plan_signature": plan_signature,
                            "task": "classification",
                            "protocol": "lodo",
                            "stage": "inner",
                            "split_key": split_key,
                            "inner_key": inner_key,
                            "repeat": 0,
                            "outer_fold": outer_fold,
                            "inner_fold": inner_fold,
                            "outer_group": str(outer_group),
                            "role": role,
                            "sample_id": sample_ids[int(index)],
                            "sample_index": int(index),
                        }
                    )
    frame = pd.DataFrame(rows)
    frame["_role_order"] = pd.Categorical(frame["role"], categories=["train", "validation", "test"], ordered=True)
    frame = frame.sort_values(
        ["repeat", "outer_fold", "stage", "inner_fold", "_role_order", "sample_index"],
        kind="stable",
    ).drop(columns="_role_order")
    return frame.reset_index(drop=True)


def write_provenance(path, feature_count):
    values = [
        ("collection", "crc_multicohort"),
        ("version", "0.2.0"),
        ("source_samples", 3589),
        ("benchmark_samples", 2941),
        ("excluded_adenoma_samples", 648),
        ("studies", 17),
        ("features", feature_count),
        ("assay", "shotgun_metagenomics"),
        ("profile_method", "MetaPhlAn4 adapted profiles"),
        ("profile_selector", "*_adapted.tsv"),
        ("abundance_unit", "percent"),
        ("abundance_transformation", "none"),
        ("normalization", "none"),
        ("scaling", "none"),
        ("prevalence_filtering", "none"),
        ("taxonomic_filtering", "none"),
        ("target", "CRC versus Control"),
        ("negative_class", "Control"),
        ("positive_class", "CRC"),
        ("excluded_phenotype", "Adenoma"),
        ("evaluation", "leave-one-dataset-out"),
        ("outer_folds", 17),
        ("inner_folds", 3),
        ("inner_grouping", "study_id"),
        ("random_state", 42),
        ("split_schema_version", 3),
    ]
    text = []
    for key, value in values:
        if isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = json.dumps(str(value))
        text.append(f"{key}: {rendered}")
    Path(path).write_text("\n".join(text) + "\n", encoding="utf-8")


def deterministic_tar(source, output):
    source = Path(source)
    output = Path(output)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as bundle:
                for path in sorted(p for p in source.rglob("*") if p.is_file()):
                    name = path.relative_to(source).as_posix()
                    data = path.read_bytes()
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mode = 0o644
                    bundle.addfile(info, io.BytesIO(data))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-zip", required=True)
    parser.add_argument("--metadata-zip", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        profiles_root = temp / "profiles"
        metadata_root = temp / "metadata"
        package = temp / "package"
        profiles_root.mkdir()
        metadata_root.mkdir()
        package.mkdir()
        with zipfile.ZipFile(args.profiles_zip) as archive:
            archive.extractall(profiles_root)
        with zipfile.ZipFile(args.metadata_zip) as archive:
            archive.extractall(metadata_root)
        profile_files = sorted(path for path in profiles_root.rglob("*_adapted.tsv") if "__MACOSX" not in path.parts)
        metadata_files = sorted(path for path in metadata_root.rglob("*.tsv") if "__MACOSX" not in path.parts)
        profile_map = {path.name.removesuffix("_adapted.tsv"): path for path in profile_files}
        metadata_map = {path.stem: path for path in metadata_files}
        if len(profile_map) != 17 or set(profile_map) != set(metadata_map):
            raise ValueError("Expected 17 matching adapted profile and metadata cohorts")
        feature_order = []
        feature_seen = set()
        metadata_blocks = []
        profile_blocks = []
        study_rows = []
        qc_rows = []
        for study_id in sorted(profile_map):
            metadata_source = pd.read_csv(metadata_map[study_id], sep="\t", dtype=str, keep_default_na=False)
            profile_source = pd.read_csv(profile_map[study_id], sep="\t", low_memory=False)
            if profile_source.columns[0] != "clade_name":
                raise ValueError(f"{profile_map[study_id].name} does not start with clade_name")
            sample_columns = [str(value) for value in profile_source.columns[1:]]
            if set(sample_columns) != set(metadata_source["Name"].astype(str)):
                raise ValueError(f"Sample mismatch in {study_id}")
            metadata_source = metadata_source.set_index("Name").loc[sample_columns].reset_index()
            disease = metadata_source["Study condition"].astype(str)
            eligible_mask = disease.isin(["Control", "CRC"])
            eligible_ids = metadata_source.loc[eligible_mask, "Name"].astype(str).tolist()
            excluded_adenoma = int((disease == "Adenoma").sum())
            source_n = len(metadata_source)
            control_n = int((disease == "Control").sum())
            crc_n = int((disease == "CRC").sum())
            selected_metadata = metadata_source.loc[eligible_mask].copy()
            standard = pd.DataFrame(
                {
                    "sampleId": selected_metadata["Name"].astype(str),
                    "subject_id": selected_metadata["Name"].astype(str),
                    "study_id": study_id,
                    "label": selected_metadata["Study condition"].map({"Control": 0, "CRC": 1}).astype(int),
                    "phenotype": selected_metadata["Study condition"].astype(str),
                    "country": selected_metadata["Country"].astype(str),
                    "body_site": selected_metadata["Body Site"].astype(str),
                    "age": selected_metadata["Age"].astype(str),
                    "bmi": selected_metadata["BMI"].astype(str),
                    "sex": selected_metadata["Sex"].astype(str),
                    "tumor_staging_ajcc": selected_metadata["Tumor Staging AJCC"].astype(str),
                    "primary_tumor_location": selected_metadata["Primary Tumor Location"].astype(str),
                }
            )
            for column in metadata_source.columns:
                standard[f"source_{snake(column)}"] = selected_metadata[column].astype(str).to_numpy()
            metadata_blocks.append(standard)
            profile_source["clade_name"] = profile_source["clade_name"].astype(str)
            if profile_source["clade_name"].duplicated().any():
                raise ValueError(f"Duplicate clade_name in {study_id}")
            for feature in profile_source["clade_name"]:
                if feature not in feature_seen:
                    feature_seen.add(feature)
                    feature_order.append(feature)
            block = profile_source.set_index("clade_name")[eligible_ids].apply(pd.to_numeric, errors="raise")
            profile_blocks.append(block)
            terminal = block.loc[block.index.to_series().str.contains("___t__", regex=False)]
            sums = terminal.sum(axis=0)
            study_rows.append(
                {
                    "study_id": study_id,
                    "profile_file": profile_map[study_id].name,
                    "metadata_file": metadata_map[study_id].name,
                    "profile_sha256": sha256_path(profile_map[study_id]),
                    "metadata_sha256": sha256_path(metadata_map[study_id]),
                    "source_n": source_n,
                    "benchmark_n": len(eligible_ids),
                    "control_n": control_n,
                    "crc_n": crc_n,
                    "adenoma_excluded_n": excluded_adenoma,
                    "single_class_outer_domain": int(control_n == 0 or crc_n == 0),
                }
            )
            qc_rows.append(
                {
                    "study_id": study_id,
                    "source_n": source_n,
                    "benchmark_n": len(eligible_ids),
                    "control_n": control_n,
                    "crc_n": crc_n,
                    "adenoma_excluded_n": excluded_adenoma,
                    "single_class_outer_domain": int(control_n == 0 or crc_n == 0),
                    "terminal_sgb_sum_min": float(sums.min()),
                    "terminal_sgb_sum_max": float(sums.max()),
                }
            )
        metadata = pd.concat(metadata_blocks, ignore_index=True)
        if len(metadata) != 2941 or metadata["sampleId"].duplicated().any():
            raise ValueError("Unexpected benchmark metadata shape or duplicate sample IDs")
        profiles = pd.concat(
            [block.reindex(feature_order, fill_value=0.0) for block in profile_blocks],
            axis=1,
        )
        profiles = profiles.loc[feature_order, metadata["sampleId"].tolist()]
        if profiles.shape != (9239, 2941):
            raise ValueError(f"Unexpected profile shape {profiles.shape}")
        values = profiles.to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Profiles contain non-finite or negative values")
        metadata.to_csv(package / "metadata.tsv", sep="\t", index=False)
        profiles.index.name = "clade_name"
        profiles.to_csv(package / "profiles.tsv", sep="\t", float_format="%.15g")
        pd.DataFrame(study_rows).to_csv(package / "study_metadata.tsv", sep="\t", index=False)
        pd.DataFrame(qc_rows).to_csv(package / "qc.tsv", sep="\t", index=False)
        write_provenance(package / "provenance.yaml", len(feature_order))
        split_dir = package / "splits" / "crc" / "mllabiome-benchmark-v2"
        split_dir.mkdir(parents=True)
        splits = split_manifest(metadata)
        splits.to_csv(split_dir / "cv_splits.tsv", sep="\t", index=False)
        required = {
            "metadata.tsv",
            "profiles.tsv",
            "provenance.yaml",
            "qc.tsv",
            "study_metadata.tsv",
            "splits/crc/mllabiome-benchmark-v2/cv_splits.tsv",
        }
        observed = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
        if observed != required:
            raise ValueError("Unexpected packaged files")
        deterministic_tar(package, output)
        summary = {
            "asset": output.name,
            "asset_sha256": sha256_path(output),
            "samples": len(metadata),
            "features": len(feature_order),
            "studies": int(metadata["study_id"].nunique()),
            "control": int((metadata["label"] == 0).sum()),
            "crc": int((metadata["label"] == 1).sum()),
            "source_samples": 3589,
            "adenoma_excluded": 648,
            "files": {name: sha256_path(package / name) for name in sorted(required)},
        }
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
