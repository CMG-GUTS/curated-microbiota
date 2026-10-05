import csv
import io
import itertools
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from curated_microbiota import collections


ROOT = Path(__file__).resolve().parents[1]

# The package manifest is always part of the source checkout and defines the
# benchmark version under test.  The large v2 release tarballs intentionally
# live outside git, so CI cannot assume ``release_assets/`` exists.
PACKAGE_MANIFEST = json.loads(
    (ROOT / "curated_microbiota" / "release-manifest.json").read_text()
)
COLLECTION_RELEASES = PACKAGE_MANIFEST["collections"]

# When a local release bundle is present (for example immediately before
# publishing), audit the actual v2 tarballs.  In an ordinary source checkout,
# fall back to the tracked v1 frozen assets and inspect exactly the repeats
# retained by benchmark v2.  CRC multicohort is new in v2 and therefore has a
# compact split-only fixture under tests/data.
LOCAL_RELEASE_DIR = ROOT / "release_assets"
LEGACY_RELEASE_DIR = ROOT / "curated-microbiota-data-v0.1.3"
LEGACY_MANIFEST_PATH = LEGACY_RELEASE_DIR / "release-manifest.json"
LEGACY_MANIFEST = (
    json.loads(LEGACY_MANIFEST_PATH.read_text())
    if LEGACY_MANIFEST_PATH.exists()
    else {"collections": {}}
)
CRC_FIXTURE = ROOT / "tests" / "data" / "crc_multicohort-v2-split-fixture.tar.gz"

SPLIT_CASES = tuple(
    (collection_name, target_name)
    for collection_name, release in COLLECTION_RELEASES.items()
    for target_name in release.get("split_sets", {})
)


def _asset_source(collection_name, target_name, split_spec):
    """Return (tar_path, split_path, retained_repeats_only).

    ``retained_repeats_only`` is true when CI is auditing the v1 source
    manifest from which v2 retained repeats 0 and 1.
    """
    current_release = COLLECTION_RELEASES[collection_name]
    current_asset = LOCAL_RELEASE_DIR / current_release["asset"]
    if current_asset.exists():
        return current_asset, split_spec["file"], False

    legacy_release = LEGACY_MANIFEST.get("collections", {}).get(collection_name)
    if legacy_release is not None:
        legacy_split = legacy_release.get("split_sets", {}).get(target_name)
        assert legacy_split is not None, (collection_name, target_name)
        legacy_asset = LEGACY_RELEASE_DIR / legacy_release["asset"]
        assert legacy_asset.exists(), f"missing tracked legacy asset: {legacy_asset}"
        return legacy_asset, legacy_split["file"], True

    assert collection_name == "crc_multicohort", collection_name
    assert CRC_FIXTURE.exists(), f"missing CI split fixture: {CRC_FIXTURE}"
    return CRC_FIXTURE, split_spec["file"], False


def _study(collection_name):
    return getattr(collections, collection_name)


def _metadata(tar, study):
    stream = tar.extractfile("metadata.tsv")
    assert stream is not None
    with io.TextIOWrapper(stream, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = {}
        for row in reader:
            sample_id = str(row[study._sample_id])
            assert sample_id not in rows, f"duplicate metadata sample_id {sample_id!r}"
            rows[sample_id] = row
    return rows


def _split_blocks(tar, split_file, *, max_repeats=None):
    stream = tar.extractfile(split_file)
    assert stream is not None
    handle = io.TextIOWrapper(stream, encoding="utf-8", newline="")
    reader = csv.DictReader(handle, delimiter="\t")
    try:
        for key, rows in itertools.groupby(
            reader,
            key=lambda row: (int(row["repeat"]), int(row["outer_fold"])),
        ):
            # benchmark-v2 deliberately retained repeats 0 and 1 from v1.
            # Consume but do not yield later legacy repeats in CI fallback mode.
            if max_repeats is not None and key[0] >= max_repeats:
                for _ in rows:
                    pass
                continue
            yield key, rows
    finally:
        handle.close()


def _add_unique(target, sample_id, context):
    assert sample_id not in target, f"duplicate sample {sample_id!r} in {context}"
    target.add(sample_id)


def _groups(sample_ids, metadata, column):
    return {metadata[sample_id][column] for sample_id in sample_ids}


def _labels(sample_ids, metadata, column):
    return Counter(metadata[sample_id][column] for sample_id in sample_ids)


def _strata(sample_ids, metadata, target_column, stratify_column):
    return Counter(
        (metadata[sample_id][target_column], metadata[sample_id][stratify_column])
        for sample_id in sample_ids
    )


def _assert_count_spread_at_most(counters, keys, maximum):
    for key in keys:
        values = [counter[key] for counter in counters]
        assert max(values) - min(values) <= maximum, (key, values)


def test_benchmark_v2_declares_two_repeat_ncv():
    assert PACKAGE_MANIFEST["benchmark"] == {
        "name": "mllabiome-benchmark",
        "version": 2,
    }
    repeated = [
        spec
        for release in COLLECTION_RELEASES.values()
        for spec in release.get("split_sets", {}).values()
        if spec["protocol"] == "repeated_nested_cv"
    ]
    assert repeated
    assert all(int(spec["repeats"]) == 2 for spec in repeated)
    assert all("mllabiome-benchmark-v2" in spec["file"] for spec in repeated)


@pytest.mark.parametrize("collection_name,target_name", SPLIT_CASES)
def test_release_split_integrity(collection_name, target_name):
    """Validate the actual frozen split manifest shipped in each release asset."""
    release = COLLECTION_RELEASES[collection_name]
    split_spec = release["split_sets"][target_name]
    study = _study(collection_name)
    target = study.target(target_name)
    asset, split_file, retained_repeats_only = _asset_source(
        collection_name, target_name, split_spec
    )

    with tarfile.open(asset, "r:gz") as tar:
        metadata = _metadata(tar, study)
        all_samples = set(metadata)
        assert len(all_samples) == study.samples

        seen_outer_blocks = set()
        test_sets_by_repeat = defaultdict(list)
        outer_class_counts = defaultdict(dict)
        inner_class_counts = defaultdict(dict)
        outer_strata_counts = defaultdict(dict)
        inner_strata_counts = defaultdict(dict)

        for (repeat, outer_fold), rows in _split_blocks(
            tar,
            split_file,
            max_repeats=int(split_spec["repeats"]) if retained_repeats_only else None,
        ):
            block_key = (repeat, outer_fold)
            assert block_key not in seen_outer_blocks, f"non-contiguous outer block {block_key}"
            seen_outer_blocks.add(block_key)

            outer = {"train": set(), "test": set()}
            inner = defaultdict(lambda: {"train": set(), "validation": set()})
            manifest_outer_groups = set()
            row_count = 0

            for row in rows:
                row_count += 1
                sample_id = str(row["sample_id"])
                assert sample_id in metadata, f"split sample absent from metadata: {sample_id}"
                assert row["protocol"] == split_spec["protocol"]
                assert int(row["repeat"]) == repeat
                assert int(row["outer_fold"]) == outer_fold

                if row["outer_group"]:
                    manifest_outer_groups.add(row["outer_group"])

                stage = row["stage"]
                role = row["role"]
                if stage == "outer":
                    assert role in outer
                    _add_unique(outer[role], sample_id, f"{collection_name}/{target_name} outer {block_key} {role}")
                elif stage == "inner":
                    inner_fold = int(row["inner_fold"])
                    assert 0 <= inner_fold < int(split_spec["inner_folds"])
                    assert role in inner[inner_fold]
                    _add_unique(
                        inner[inner_fold][role],
                        sample_id,
                        f"{collection_name}/{target_name} inner {block_key}/{inner_fold} {role}",
                    )
                else:
                    raise AssertionError(f"unexpected split stage {stage!r}")

            assert row_count > 0
            assert outer["train"]
            assert outer["test"]
            assert outer["train"].isdisjoint(outer["test"])
            assert outer["train"] | outer["test"] == all_samples

            expected_inner_folds = set(range(int(split_spec["inner_folds"])))
            assert set(inner) == expected_inner_folds
            validation_sets = []
            for inner_fold in sorted(inner):
                train = inner[inner_fold]["train"]
                validation = inner[inner_fold]["validation"]
                assert train
                assert validation
                assert train.isdisjoint(validation)
                assert train | validation == outer["train"]
                validation_sets.append(validation)

                if target.task == "classification":
                    train_labels = set(_labels(outer["train"], metadata, target.column))
                    validation_labels = set(_labels(validation, metadata, target.column))
                    assert validation_labels == train_labels
                    inner_class_counts[(repeat, outer_fold)][inner_fold] = _labels(
                        validation, metadata, target.column
                    )

                if split_spec["inner_grouping"] == "outer_group":
                    group_column = study._group
                    assert group_column is not None
                    assert _groups(train, metadata, group_column).isdisjoint(
                        _groups(validation, metadata, group_column)
                    )
                elif split_spec["inner_grouping"] == "subject":
                    subject_column = study._subject
                    assert subject_column is not None
                    assert _groups(train, metadata, subject_column).isdisjoint(
                        _groups(validation, metadata, subject_column)
                    )

                explicit_group = split_spec.get("group_col")
                if explicit_group:
                    assert _groups(train, metadata, explicit_group).isdisjoint(
                        _groups(validation, metadata, explicit_group)
                    )

                stratify_column = split_spec.get("stratify_col")
                if stratify_column and target.task == "classification":
                    inner_strata_counts[(repeat, outer_fold)][inner_fold] = _strata(
                        validation, metadata, target.column, stratify_column
                    )

            # Inner validation folds must partition the corresponding outer-training set.
            for left, right in itertools.combinations(validation_sets, 2):
                assert left.isdisjoint(right)
            assert set().union(*validation_sets) == outer["train"]

            # LODO means the complete held-out domain is the outer test fold.
            if split_spec["protocol"] == "lodo":
                group_column = study._group
                assert group_column is not None
                train_groups = _groups(outer["train"], metadata, group_column)
                test_groups = _groups(outer["test"], metadata, group_column)
                assert len(test_groups) == 1
                assert train_groups.isdisjoint(test_groups)
                assert manifest_outer_groups == test_groups

            # Explicit group-aware NCV (PRIME PTSD) must also be leakage-free outside.
            explicit_group = split_spec.get("group_col")
            if explicit_group:
                assert _groups(outer["train"], metadata, explicit_group).isdisjoint(
                    _groups(outer["test"], metadata, explicit_group)
                )

            if target.task == "classification":
                outer_class_counts[repeat][outer_fold] = _labels(
                    outer["test"], metadata, target.column
                )

            stratify_column = split_spec.get("stratify_col")
            if stratify_column and target.task == "classification":
                outer_strata_counts[repeat][outer_fold] = _strata(
                    outer["test"], metadata, target.column, stratify_column
                )

            test_sets_by_repeat[repeat].append(outer["test"])

        expected_repeats = set(range(int(split_spec["repeats"])))
        expected_outer_folds = set(range(int(split_spec["outer_folds"])))
        assert {repeat for repeat, _ in seen_outer_blocks} == expected_repeats
        for repeat in expected_repeats:
            folds = {outer for r, outer in seen_outer_blocks if r == repeat}
            assert folds == expected_outer_folds

            # Each sample must be tested exactly once in each repeat.
            tests = test_sets_by_repeat[repeat]
            for left, right in itertools.combinations(tests, 2):
                assert left.isdisjoint(right)
            assert set().union(*tests) == all_samples

        if target.task != "classification":
            return

        all_classes = set(_labels(all_samples, metadata, target.column))

        if split_spec["protocol"] == "repeated_nested_cv" and not split_spec.get("group_col"):
            # Ordinary StratifiedKFold-style NCV: each class is distributed as evenly
            # as arithmetically possible across both outer and inner validation folds.
            for repeat in expected_repeats:
                counters = [
                    outer_class_counts[repeat][fold]
                    for fold in sorted(expected_outer_folds)
                ]
                assert all(set(counter) == all_classes for counter in counters)
                _assert_count_spread_at_most(counters, all_classes, 1)

            for key, fold_counts in inner_class_counts.items():
                counters = [fold_counts[fold] for fold in sorted(fold_counts)]
                assert all(set(counter) == all_classes for counter in counters)
                _assert_count_spread_at_most(counters, all_classes, 1)

        if split_spec.get("stratify_col"):
            # Group-aware PRIME NCV balances the label x time-point strata while
            # preserving subject integrity. Outer strata differ by at most one sample;
            # the grouped inner folds allow at most a two-sample spread.
            global_strata = set(
                _strata(all_samples, metadata, target.column, split_spec["stratify_col"])
            )
            for repeat in expected_repeats:
                counters = [
                    outer_strata_counts[repeat][fold]
                    for fold in sorted(expected_outer_folds)
                ]
                assert all(set(counter) == global_strata for counter in counters)
                _assert_count_spread_at_most(counters, global_strata, 1)

            for key, fold_counts in inner_strata_counts.items():
                counters = [fold_counts[fold] for fold in sorted(fold_counts)]
                outer_train = sum(counters, Counter())
                expected_strata = set(outer_train)
                assert all(set(counter) == expected_strata for counter in counters)
                _assert_count_spread_at_most(counters, expected_strata, 2)
