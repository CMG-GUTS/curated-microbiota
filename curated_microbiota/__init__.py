from . import collections
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

from importlib.metadata import version

__version__ = version("curated-microbiota")

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
]
