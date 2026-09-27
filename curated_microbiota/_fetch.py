from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.parse import quote
from urllib.request import urlopen

from platformdirs import user_cache_path

from ._errors import ChecksumError


def _root() -> Path:
    return Path(os.getenv("CURATED_MICROBIOTA_CACHE", user_cache_path("curated-microbiota")))


def _base() -> str:
    return os.getenv(
        "CURATED_MICROBIOTA_RELEASE_URL",
        "https://github.com/CMG-GUTS/curated-microbiota/releases/download/data-v0.1.0",
    ).rstrip("/")


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _url(asset: str) -> str:
    return f"{_base()}/{quote(asset)}"


def _valid(root: Path, files: tuple[tuple[str, str], ...]) -> bool:
    return all((root / name).is_file() and _digest(root / name) == sha256 for name, sha256 in files)


def fetch(study: str, version: str, asset: str, asset_sha256: str, files: tuple[tuple[str, str], ...]) -> Path:
    target = _root() / study / version
    if _valid(target, files):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(_url(asset)) as source, NamedTemporaryFile(dir=target.parent, delete=False) as sink:
        shutil.copyfileobj(source, sink)
        archive = Path(sink.name)
    value = _digest(archive)
    if value != asset_sha256:
        archive.unlink(missing_ok=True)
        raise ChecksumError(f"{study}/{asset}: {value} != {asset_sha256}")
    with TemporaryDirectory(dir=target.parent) as temporary:
        staging = Path(temporary)
        with tarfile.open(archive, "r:gz") as bundle:
            members = {member.name: member for member in bundle.getmembers()}
            if set(members) != {name for name, _ in files}:
                archive.unlink(missing_ok=True)
                raise ChecksumError(f"{study}/{asset}: unexpected archive contents")
            for name, sha256 in files:
                member = members[name]
                if not member.isfile():
                    archive.unlink(missing_ok=True)
                    raise ChecksumError(f"{study}/{asset}: invalid member {name}")
                source = bundle.extractfile(member)
                if source is None:
                    archive.unlink(missing_ok=True)
                    raise ChecksumError(f"{study}/{asset}: unreadable member {name}")
                destination = staging / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("wb") as sink:
                    shutil.copyfileobj(source, sink)
                value = _digest(destination)
                if value != sha256:
                    archive.unlink(missing_ok=True)
                    raise ChecksumError(f"{study}/{name}: {value} != {sha256}")
        target.mkdir(parents=True, exist_ok=True)
        for name, _ in files:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            (staging / name).replace(destination)
    archive.unlink(missing_ok=True)
    return target


def cached(study: str, version: str, files: tuple[tuple[str, str], ...]) -> bool:
    return _valid(_root() / study / version, files)
