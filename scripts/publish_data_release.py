import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def run(args, capture=False, check=True):
    return subprocess.run(args, text=True, capture_output=capture, check=check)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="CMG-GUTS/curated-microbiota")
    parser.add_argument("--previous", default="data-v0.1.3")
    parser.add_argument("--release", default="data-v0.1.4")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    assets_dir = root / "release_assets"
    manifest_path = root / "curated_microbiota" / "release-manifest.json"
    sums_path = assets_dir / "SHA256SUMS"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["release"] != args.release:
        raise SystemExit("Release tag does not match release-manifest.json")
    expected = {value["asset"]: value["sha256"] for value in manifest["collections"].values()}
    new_asset = assets_dir / "crc_multicohort-0.1.0.tar.gz"
    if sha256(new_asset) != expected[new_asset.name]:
        raise SystemExit("New CRC asset checksum mismatch")
    if shutil.which("gh") is None:
        raise SystemExit("GitHub CLI gh is required")
    run(["gh", "auth", "status"], check=True)
    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        run(["gh", "release", "download", args.previous, "--repo", args.repo, "--pattern", "*.tar.gz", "--dir", str(temp)])
        old_expected = {name: digest for name, digest in expected.items() if name != new_asset.name}
        observed = {path.name for path in temp.glob("*.tar.gz")}
        if observed != set(old_expected):
            missing = sorted(set(old_expected) - observed)
            extra = sorted(observed - set(old_expected))
            raise SystemExit(f"Previous-release asset set mismatch; missing={missing}, extra={extra}")
        for name, digest in old_expected.items():
            if sha256(temp / name) != digest:
                raise SystemExit(f"Checksum mismatch for {name}")
        shutil.copy2(new_asset, temp / new_asset.name)
        shutil.copy2(manifest_path, temp / "release-manifest.json")
        shutil.copy2(sums_path, temp / "SHA256SUMS")
        assets = [str(temp / name) for name in sorted(expected)] + [str(temp / "release-manifest.json"), str(temp / "SHA256SUMS")]
        existing = run(["gh", "release", "view", args.release, "--repo", args.repo], capture=True, check=False).returncode == 0
        if existing:
            run(["gh", "release", "upload", args.release, "--repo", args.repo, "--clobber", *assets])
            run(["gh", "release", "edit", args.release, "--repo", args.repo, "--title", "Data v0.1.4", "--notes", "Adds crc_multicohort-0.1.0 and republishes the complete pinned data asset set.", f"--draft={'false' if args.publish else 'true'}"])
        else:
            command = ["gh", "release", "create", args.release, "--repo", args.repo, "--title", "Data v0.1.4", "--notes", "Adds crc_multicohort-0.1.0 and republishes the complete pinned data asset set."]
            if not args.publish:
                command.append("--draft")
            command.extend(assets)
            run(command)
    print(f"{args.release} {'published' if args.publish else 'created/updated as draft'}")


if __name__ == "__main__":
    main()
