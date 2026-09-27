from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache(maxsize=1)
def release_manifest() -> dict[str, Any]:
    resource = files("curated_microbiota").joinpath("release-manifest.json")
    with resource.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def data_release() -> str:
    return str(release_manifest()["release"])


def collection_release(name: str) -> dict[str, Any]:
    collections = release_manifest()["collections"]
    try:
        return dict(collections[name])
    except KeyError as exc:
        raise KeyError(f"Collection {name!r} is missing from the packaged release manifest") from exc
