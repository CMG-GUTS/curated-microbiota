from ._registry import (
    brown_mdd,
    crc_multicohort,
    healthy_colombia,
    ibd_multiclass,
    lampp_crc,
    metaibs_ibs,
    prime_ptsd,
    lampp_dm7,
    lampp_dm90,
    lampp_ghs,
    lampp_ibd,
    lampp_scz,
    prjna1190316,
    studies,
)
from .study import Study


def available(
    *,
    condition: str | None = None,
    assay: str | None = None,
    role: str | None = None,
    status: str | None = None,
    target: str | None = None,
    benchmark: bool | None = None,
    problem_type: str | None = None,
) -> tuple[Study, ...]:
    return tuple(
        study
        for study in studies
        if (condition is None or study.condition == condition)
        and (assay is None or study.assay == assay)
        and (role is None or study.role == role)
        and (status is None or study.status == status)
        and (target is None or target in study.targets)
        and (benchmark is None or bool(study.benchmark_targets) is benchmark)
        and (problem_type is None or any(target.problem_type == problem_type for target in study.benchmark_target_info))
    )


__all__ = [
    "available",
    "brown_mdd",
    "crc_multicohort",
    "healthy_colombia",
    "ibd_multiclass",
    "lampp_crc",
    "metaibs_ibs",
    "prime_ptsd",
    "lampp_dm7",
    "lampp_dm90",
    "lampp_ghs",
    "lampp_ibd",
    "lampp_scz",
    "prjna1190316",
]
