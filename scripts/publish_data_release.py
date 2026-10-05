import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


DEFAULT_RELEASE = "data-v0.2.0"


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
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    assets_dir = root / "release_assets"
    manifest_path = root / "curated_microbiota" / "release-manifest.json"
    release_manifest_path = assets_dir / "release-manifest.json"
    sums_path = assets_dir / "SHA256SUMS"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["release"] != args.release:
        raise SystemExit("Release tag does not match release-manifest.json")
    if manifest["benchmark"] != {"name": "mllabiome-benchmark", "version": 2}:
        raise SystemExit("Expected mllabiome-benchmark-v2")

    expected = {value["asset"]: value["sha256"] for value in manifest["collections"].values()}
    observed = {path.name for path in assets_dir.glob("*.tar.gz")}
    if observed != set(expected):
        raise SystemExit(f"Local release asset set mismatch; expected={sorted(expected)}, observed={sorted(observed)}")
    for name, digest in expected.items():
        if sha256(assets_dir / name) != digest:
            raise SystemExit(f"Asset checksum mismatch for {name}")
    if release_manifest_path.read_bytes() != manifest_path.read_bytes():
        raise SystemExit("release_assets/release-manifest.json is not synchronized")

    if shutil.which("gh") is None:
        raise SystemExit("GitHub CLI gh is required")
    run(["gh", "auth", "status"], check=True)

    assets = [str(assets_dir / name) for name in sorted(expected)] + [str(release_manifest_path), str(sums_path)]
    title = "Data v0.2.0"
    notes = (
        "Introduces mllabiome-benchmark-v2. Repeated nested cross-validation now uses "
        "5 outer folds x 3 inner folds x 2 repeats; historical benchmark-v1 releases remain unchanged."
    )
    existing = run(["gh", "release", "view", args.release, "--repo", args.repo], capture=True, check=False).returncode == 0
    if existing:
        run(["gh", "release", "upload", args.release, "--repo", args.repo, "--clobber", *assets])
        command = ["gh", "release", "edit", args.release, "--repo", args.repo, "--title", title, "--notes", notes]
        if args.publish:
            command.append("--draft=false")
        run(command)
    else:
        command = ["gh", "release", "create", args.release, "--repo", args.repo, "--title", title, "--notes", notes]
        if not args.publish:
            command.append("--draft")
        command.extend(assets)
        run(command)
    print(f"{args.release} {'published' if args.publish else 'created/updated as draft'}")


if __name__ == "__main__":
    main()
