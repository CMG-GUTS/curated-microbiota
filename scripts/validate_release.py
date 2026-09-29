import hashlib
import json
import tarfile
from pathlib import Path


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "curated_microbiota" / "release-manifest.json").read_text(encoding="utf-8"))
    if manifest["release"] != "data-v0.1.4":
        raise SystemExit("Unexpected data release")
    entry = manifest["collections"]["crc_multicohort"]
    archive = root / "release_assets" / entry["asset"]
    if sha256(archive) != entry["sha256"]:
        raise SystemExit("CRC archive checksum mismatch")
    with tarfile.open(archive, "r:gz") as handle:
        names = sorted(member.name for member in handle.getmembers() if member.isfile())
        expected = sorted(entry["files"])
        if names != expected:
            raise SystemExit(f"CRC archive file set mismatch: {names}")
        for name, digest in entry["files"].items():
            member = handle.extractfile(name)
            if member is None:
                raise SystemExit(f"Missing {name}")
            value = hashlib.sha256(member.read()).hexdigest()
            if value != digest:
                raise SystemExit(f"Checksum mismatch for {name}")
    print("Release validation passed")


if __name__ == "__main__":
    main()
