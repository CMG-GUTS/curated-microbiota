import csv
import hashlib
import json
import tarfile
from pathlib import Path


EXPECTED_RELEASE = "data-v0.2.0"
EXPECTED_BENCHMARK = "mllabiome-benchmark-v2"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest(payload: dict[str, object]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def expected_plan_signature(collection: str, split: dict[str, object]) -> str:
    return digest(
        {
            "schema_version": 3,
            "protocol": split["protocol"],
            "outer_folds": split["outer_folds"],
            "inner_folds": split["inner_folds"],
            "repeats": split["repeats"],
            "random_state": split["random_state"],
            "group_col": "subject_id" if collection == "prime_ptsd" else None,
            "stratify_col": "time_point" if collection == "prime_ptsd" else None,
            "inner_grouping": split["inner_grouping"],
        }
    )


def validate_split(collection: str, split: dict[str, object], payload: bytes) -> None:
    if split["benchmark"] != EXPECTED_BENCHMARK:
        raise SystemExit(f"{collection}: unexpected benchmark id")
    if "mllabiome-benchmark-v2" not in str(split["file"]):
        raise SystemExit(f"{collection}: split path is not benchmark-v2")
    if split["protocol"] == "repeated_nested_cv":
        rows = list(csv.DictReader(payload.decode("utf-8").splitlines(), delimiter="\t"))
        if not rows:
            raise SystemExit(f"{collection}: empty split manifest")
        if split["repeats"] != 2:
            raise SystemExit(f"{collection}: repeated NCV must use two repeats")
        repeats = sorted({int(row["repeat"]) for row in rows})
        if repeats != [0, 1]:
            raise SystemExit(f"{collection}: split manifest repeats are {repeats}, expected [0, 1]")
        signatures = {row["plan_signature"] for row in rows}
        expected = expected_plan_signature(collection, split)
        if signatures != {expected}:
            raise SystemExit(f"{collection}: split plan signature mismatch")
    elif split["repeats"] != 1:
        raise SystemExit(f"{collection}: non-repeated design must retain repeats=1")


def main():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "curated_microbiota" / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["release"] != EXPECTED_RELEASE:
        raise SystemExit(f"Unexpected data release: {manifest['release']}")
    benchmark = manifest["benchmark"]
    if benchmark != {"name": "mllabiome-benchmark", "version": 2}:
        raise SystemExit(f"Unexpected benchmark: {benchmark}")

    assets_dir = root / "release_assets"
    expected_assets = {entry["asset"] for entry in manifest["collections"].values()}
    observed_assets = {path.name for path in assets_dir.glob("*.tar.gz")}
    if observed_assets != expected_assets:
        missing = sorted(expected_assets - observed_assets)
        extra = sorted(observed_assets - expected_assets)
        raise SystemExit(f"Release asset set mismatch; missing={missing}, extra={extra}")

    for collection, entry in manifest["collections"].items():
        if entry["version"] != "0.2.0":
            raise SystemExit(f"{collection}: collection version is not 0.2.0")
        archive = assets_dir / entry["asset"]
        if sha256(archive) != entry["sha256"]:
            raise SystemExit(f"{collection}: archive checksum mismatch")
        with tarfile.open(archive, "r:gz") as handle:
            expected_files = dict(entry["files"])
            split_names = {str(split["file"]) for split in entry.get("split_sets", {}).values() if split["protocol"] == "repeated_nested_cv"}
            retained: dict[str, bytes] = {}
            observed_files: set[str] = set()
            for member in handle:
                if not member.isfile():
                    continue
                name = member.name
                observed_files.add(name)
                if name not in expected_files:
                    raise SystemExit(f"{collection}: unexpected archive member {name}")
                source = handle.extractfile(member)
                if source is None:
                    raise SystemExit(f"{collection}: unreadable {name}")
                value = hashlib.sha256()
                capture = name == "provenance.yaml" or name in split_names
                chunks: list[bytes] | None = [] if capture else None
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    value.update(block)
                    if chunks is not None:
                        chunks.append(block)
                if value.hexdigest() != expected_files[name]:
                    raise SystemExit(f"{collection}: checksum mismatch for {name}")
                if chunks is not None:
                    retained[name] = b"".join(chunks)
            if observed_files != set(expected_files):
                missing = sorted(set(expected_files) - observed_files)
                raise SystemExit(f"{collection}: missing archive files {missing}")
            provenance = retained.get("provenance.yaml", b"").decode("utf-8", errors="replace")
            if "mllabiome-benchmark-v1" in provenance:
                raise SystemExit(f"{collection}: provenance still references benchmark v1")
            for split in entry.get("split_sets", {}).values():
                payload = retained.get(str(split["file"]), b"")
                validate_split(collection, split, payload)

    release_copy = assets_dir / "release-manifest.json"
    if release_copy.read_bytes() != manifest_path.read_bytes():
        raise SystemExit("release_assets/release-manifest.json is not synchronized")
    print("Release validation passed")


if __name__ == "__main__":
    main()
