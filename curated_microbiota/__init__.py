from importlib.metadata import PackageNotFoundError, version

from . import collections
from ._manifest import data_release
from .study import (
    Benchmark,
    EvaluationDesign,
    ExternalSet,
    MLLABIOME_BENCHMARK,
    MLLABIOME_NCV,
    Sequencing,
    Source,
    SplitSet,
    Study,
    Target,
)

try:
    __version__ = version("curated-microbiota")
except PackageNotFoundError:
    __version__ = "0.1.2"

__data_release__ = data_release()

__all__ = [
    "Benchmark",
    "EvaluationDesign",
    "ExternalSet",
    "MLLABIOME_BENCHMARK",
    "MLLABIOME_NCV",
    "Sequencing",
    "Source",
    "SplitSet",
    "Study",
    "Target",
    "collections",
    "__version__",
    "__data_release__",
]
