import gzip
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from curated_microbiota import collections


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_MANIFEST = json.loads(
    (ROOT / "curated_microbiota" / "release-manifest.json").read_text()
)
COLLECTION_RELEASES = PACKAGE_MANIFEST["collections"]
FIXTURE_PATH = ROOT / "tests" / "data" / "benchmark-v2-split-fixture.json.gz"

with gzip.open(FIXTURE_PATH, "rt", encoding="utf-8") as handle:
    SPLIT_FIXTURE = json.load(handle)

SPLIT_CASES = tuple(
    (collection_name, target_name)
    for collection_name, release in COLLECTION_RELEASES.items()
    for target_name in release.get("split_sets", {})
)


def _study(collection_name):
    return getattr(collections, collection_name)


def _groups(sample_indices, metadata, column):
    return {metadata[index][column] for index in sample_indices}


def _labels(sample_indices, metadata, column):
    return Counter(metadata[index][column] for index in sample_indices)


def _strata(sample_indices, metadata, target_column, stratify_column):
    return Counter(
        (metadata[index][target_column], metadata[index][stratify_column])
        for index in sample_indices
    )


def _assert_count_spread_at_most(counters, keys, maximum):
    for key in keys:
        values = [counter[key] for counter in counters]
        assert max(values) - min(values) <= maximum, (key, values)


def test_split_fixture_matches_packaged_benchmark_release():
    """The hermetic CI fixture must describe the exact packaged v2 split files."""
    assert SPLIT_FIXTURE["benchmark"] == PACKAGE_MANIFEST["benchmark"]
    assert set(SPLIT_FIXTURE["collections"]) == set(COLLECTION_RELEASES)

    for collection_name, release in COLLECTION_RELEASES.items():
        fixture = SPLIT_FIXTURE["collections"][collection_name]
        assert fixture["asset"] == release["asset"]
        assert fixture["asset_sha256"] == release["sha256"]
        assert fixture["metadata_sha256"] == release["files"]["metadata.tsv"]
        assert set(fixture["targets"]) == set(release.get("split_sets", {}))
        for target_name, split_spec in release.get("split_sets", {}).items():
            assert (
                fixture["targets"][target_name]["split_sha256"]
                == release["files"][split_spec["file"]]
            )


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
    """Validate the frozen v2 partitions without depending on untracked release tarballs."""
    release = COLLECTION_RELEASES[collection_name]
    split_spec = release["split_sets"][target_name]
    study = _study(collection_name)
    target = study.target(target_name)

    collection_fixture = SPLIT_FIXTURE["collections"][collection_name]
    samples = collection_fixture["samples"]
    metadata = collection_fixture["metadata"]
    blocks = collection_fixture["targets"][target_name]["blocks"]

    assert len(samples) == len(set(samples)) == study.samples
    assert len(metadata) == len(samples)
    all_samples = set(range(len(samples)))

    seen_outer_blocks = set()
    test_sets_by_repeat = defaultdict(list)
    outer_class_counts = defaultdict(dict)
    inner_class_counts = defaultdict(dict)
    outer_strata_counts = defaultdict(dict)
    inner_strata_counts = defaultdict(dict)

    for block in blocks:
        repeat = int(block["repeat"])
        outer_fold = int(block["outer_fold"])
        block_key = (repeat, outer_fold)
        assert block_key not in seen_outer_blocks, f"duplicate outer block {block_key}"
        seen_outer_blocks.add(block_key)

        outer = {
            "train": set(block["outer"]["train"]),
            "test": set(block["outer"]["test"]),
        }
        assert outer["train"]
        assert outer["test"]
        assert outer["train"].isdisjoint(outer["test"])
        assert outer["train"] | outer["test"] == all_samples

        inner = {
            int(inner_fold): {
                "train": set(roles["train"]),
                "validation": set(roles["validation"]),
            }
            for inner_fold, roles in block["inner"].items()
        }
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
                inner_class_counts[block_key][inner_fold] = _labels(
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
                inner_strata_counts[block_key][inner_fold] = _strata(
                    validation, metadata, target.column, stratify_column
                )

        # Inner validation folds must partition the corresponding outer-training set.
        for left, right in itertools.combinations(validation_sets, 2):
            assert left.isdisjoint(right)
        assert set().union(*validation_sets) == outer["train"]

        # LODO must hold out exactly one complete domain/study at the outer level.
        if split_spec["protocol"] == "lodo":
            group_column = study._group
            assert group_column is not None
            train_groups = _groups(outer["train"], metadata, group_column)
            test_groups = _groups(outer["test"], metadata, group_column)
            assert len(test_groups) == 1
            assert train_groups.isdisjoint(test_groups)
            assert set(block.get("outer_groups", [])) == test_groups

        # Explicit group-aware NCV (PRIME PTSD) must be leakage-free outside too.
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

        tests = test_sets_by_repeat[repeat]
        for left, right in itertools.combinations(tests, 2):
            assert left.isdisjoint(right)
        assert set().union(*tests) == all_samples

    if target.task != "classification":
        return

    all_classes = set(_labels(all_samples, metadata, target.column))

    if split_spec["protocol"] == "repeated_nested_cv" and not split_spec.get(
        "group_col"
    ):
        # Ordinary StratifiedKFold-style NCV: distribute each class as evenly as
        # arithmetically possible across outer and inner validation folds.
        for repeat in expected_repeats:
            counters = [
                outer_class_counts[repeat][fold]
                for fold in sorted(expected_outer_folds)
            ]
            assert all(set(counter) == all_classes for counter in counters)
            _assert_count_spread_at_most(counters, all_classes, 1)

        for fold_counts in inner_class_counts.values():
            counters = [fold_counts[fold] for fold in sorted(fold_counts)]
            assert all(set(counter) == all_classes for counter in counters)
            _assert_count_spread_at_most(counters, all_classes, 1)

    if split_spec.get("stratify_col"):
        # Group-aware PRIME NCV balances label x time-point strata while preserving
        # subject integrity. Outer strata differ by at most one sample; grouped inner
        # folds allow at most a two-sample spread.
        global_strata = set(
            _strata(
                all_samples,
                metadata,
                target.column,
                split_spec["stratify_col"],
            )
        )
        for repeat in expected_repeats:
            counters = [
                outer_strata_counts[repeat][fold]
                for fold in sorted(expected_outer_folds)
            ]
            assert all(set(counter) == global_strata for counter in counters)
            _assert_count_spread_at_most(counters, global_strata, 1)

        for fold_counts in inner_strata_counts.values():
            counters = [fold_counts[fold] for fold in sorted(fold_counts)]
            outer_train = sum(counters, Counter())
            expected_strata = set(outer_train)
            assert all(set(counter) == expected_strata for counter in counters)
            _assert_count_spread_at_most(counters, expected_strata, 2)
