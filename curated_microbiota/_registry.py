from ._manifest import collection_release
from .study import (
    EvaluationDesign,
    MLLABIOME_BENCHMARK,
    MLLABIOME_NCV,
    Sequencing,
    Source,
    Study,
    _External,
    _File,
    _Split,
    _Target,
)


def _files(values: dict[str, str]) -> tuple[_File, ...]:
    return tuple(_File(name, sha256) for name, sha256 in values.items())


def _release(name: str) -> dict[str, object]:
    value = collection_release(name)
    return {
        "version": str(value["version"]),
        "_asset": str(value["asset"]),
        "_asset_sha256": str(value["sha256"]),
        "_files": _files(dict(value["files"])),
    }



PRIME = Source(
    name="PRIME",
    title="PRIME: a database for 16S rRNA microbiome data with phenotypic reference and comprehensive metadata",
    doi="10.1093/nar/gkaf1057",
    url="https://primedb.sjtu.edu.cn/",
)

METAIBS = Source(
    name="MetaIBS",
    title="MetaIBS: large-scale amplicon-based meta analysis of irritable bowel syndrome",
    doi="10.1101/2024.01.22.575775",
    url="https://github.com/bio-datascience/MetaIBS",
)

LAMPP = Source(
    name="LAMPP",
    title="LAMPP: A benchmark for continuous evaluation of host phenotype prediction from shotgun metagenomic data",
    doi="10.1101/2025.06.12.658885",
    url="https://lampp.yassourlab.com/",
)


brown_mdd = Study(
    name="brown_mdd",
    title="Brown MDD",
    **_release("brown_mdd"),
    accession="PRJNA591924",
    condition="depression",
    assay="16s_v4",
    role="diagnosis",
    status="ready",
    samples=90,
    features=569,
    population="American young adults aged 18-25",
    country="United States",
    sample_type="stool",
    sequencing=Sequencing(
        assay="16S rRNA amplicon",
        region="V4",
        forward_primer="515F",
        reverse_primer="806R",
        platform="Illumina",
        instrument="MiSeq",
        layout="paired-end",
        read_length="2x250 bp",
    ),
    confounders=("age", "sex"),
    _targets=(
        _Target("mdd", "target_mdd", "classification", 1, ("control", "mdd"), ((0, 0), (1, 1))),
        _Target("promis_depression", "target_depression_severity", "regression"),
    ),
    _splits=(
        _Split("mdd", MLLABIOME_BENCHMARK, MLLABIOME_NCV, "splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv"),
        _Split("promis_depression", MLLABIOME_BENCHMARK, MLLABIOME_NCV, "splits/promis_depression/mllabiome-benchmark-v1/cv_splits.tsv"),
    ),
    _default="mdd",
)


prjna1190316 = Study(
    name="prjna1190316",
    title="PRJNA1190316 adolescent MDD",
    **_release("prjna1190316"),
    accession="PRJNA1190316",
    condition="depression",
    assay="16s_v3_v4",
    role="diagnosis",
    status="ready",
    samples=90,
    features=881,
    population="First-episode drug-naive adolescents with MDD and age-/sex-matched healthy controls",
    country="China",
    sample_type="stool",
    sequencing=Sequencing(
        assay="16S rRNA amplicon",
        region="V3-V4",
        forward_primer="338F",
        reverse_primer="806R",
        platform="Illumina",
        instrument="NextSeq 2000",
        layout="paired-end",
        read_length="2x300 bp",
    ),
    _targets=(_Target("mdd", "target_mdd", "classification", 1, ("control", "mdd"), ((0, 0), (1, 1))),),
    _splits=(_Split("mdd", MLLABIOME_BENCHMARK, MLLABIOME_NCV, "splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv"),),
    _default="mdd",
    _subject="sample_id",
)


healthy_colombia = Study(
    name="healthy_colombia",
    title="Healthy Colombian men",
    **_release("healthy_colombia"),
    accession="PRJNA1000574",
    condition="healthy",
    assay="16s_v3_v4",
    role="reference",
    status="ready",
    samples=88,
    features=670,
    population="Healthy Colombian men aged 21-40 years",
    country="Colombia",
    sample_type="stool",
    sequencing=Sequencing(
        assay="16S rRNA amplicon",
        region="V3-V4",
        forward_primer="Bakt_341F",
        reverse_primer="Bakt_805R",
        platform="Illumina",
        instrument="MiSeq",
        layout="paired-end",
        read_length="2x300 bp",
    ),
)


def _lampp(
    name: str,
    title: str,
    condition: str,
    samples: int,
    features: int,
    design: EvaluationDesign,
    group: str | None,
) -> Study:
    task = name.removeprefix("lampp_")
    return Study(
        name=name,
        title=title,
        **_release(name),
        accession=f"LAMPP:{task}",
        condition=condition,
        assay="shotgun_metagenomics",
        role="benchmark",
        status="ready",
        samples=samples,
        features=features,
        population="LAMPP host-phenotype benchmark task",
        sample_type="gut metagenome",
        sequencing=Sequencing(
            assay="Shotgun metagenomics",
            platform="Source-study dependent",
            instrument="Source-study dependent",
            layout="Source-study dependent",
        ),
        source=LAMPP,
        _targets=(_Target(task, "label", "classification", 1, ("0", "1"), ((0, 0), (1, 1))),),
        _splits=(_Split(task, MLLABIOME_BENCHMARK, design, f"splits/{task}/mllabiome-benchmark-v1/cv_splits.tsv"),),
        _external=_External("test_profiles.tsv", "test_metadata.tsv", False, "LAMPP leaderboard"),
        _default=task,
        _abundance="profiles.tsv",
        _feature_metadata=None,
        _format="metaphlan_tsv",
        _sample_id="sampleId",
        _subject="subject_id",
        _group=group,
    )
metaibs_ibs = Study(
    name="metaibs_ibs",
    title="MetaIBS fecal IBS",
    **_release("metaibs_ibs"),
    accession="MetaIBS:stool-six-study",
    condition="irritable_bowel_syndrome",
    assay="16s_multi_region",
    role="benchmark",
    status="ready",
    samples=1671,
    features=1668,
    population="Adults with IBS and healthy controls across six MetaIBS source studies",
    country="Multi-country",
    sample_type="stool",
    sequencing=Sequencing(
        assay="16S rRNA amplicon",
        region="Source-study dependent",
        platform="Source-study dependent",
        instrument="Source-study dependent",
        layout="Source-study dependent",
    ),
    source=METAIBS,
    _targets=(_Target("ibs", "label", "classification", 1, ("Healthy", "IBS"), ((0, 0), (1, 1))),),
    _splits=(
        _Split(
            "ibs",
            MLLABIOME_BENCHMARK,
            EvaluationDesign("lodo", 6, 3, 1, 42, "outer_group"),
            "splits/ibs/mllabiome-benchmark-v1/cv_splits.tsv",
        ),
    ),
    _default="ibs",
    _abundance="profiles.tsv",
    _feature_metadata=None,
    _format="metaphlan_tsv",
    _sample_id="sampleId",
    _subject="subject_id",
    _group="study_id",
)


prime_ptsd = Study(
    name="prime_ptsd",
    title="PRIME PTSD prebiotic trial",
    **_release("prime_ptsd"),
    accession="PRJNA1086950",
    condition="posttraumatic_stress_disorder",
    assay="16s_v4",
    role="benchmark",
    status="ready",
    samples=169,
    features=294,
    population="Veterans with clinician-verified PTSD in a 12-week randomized prebiotic-versus-placebo trial",
    country="United States",
    sample_type="stool",
    sequencing=Sequencing(
        assay="16S rRNA amplicon",
        region="V4",
        forward_primer="CS1_515F",
        reverse_primer="CS2_806R",
        platform="Illumina",
        instrument="MiniSeq",
        layout="paired-end",
        read_length="2x154 bp",
    ),
    source=PRIME,
    confounders=("sex", "time_point"),
    _targets=(_Target("intervention", "label", "classification", 1, ("Placebo", "Prebiotic"), ((0, 0), (1, 1))),),
    _splits=(
        _Split(
            "intervention",
            MLLABIOME_BENCHMARK,
            MLLABIOME_NCV,
            "splits/intervention/mllabiome-benchmark-v1/cv_splits.tsv",
        ),
    ),
    _default="intervention",
    _abundance="profiles.tsv",
    _feature_metadata=None,
    _format="metaphlan_tsv",
    _sample_id="sampleId",
    _subject="subject_id",
    _group="subject_id",
    _stratify="time_point",
)


lampp_scz = _lampp(
    "lampp_scz",
    "LAMPP schizophrenia",
    "schizophrenia",
    119,
    3130,
    MLLABIOME_NCV,
    None,
)

lampp_crc = _lampp(
    "lampp_crc",
    "LAMPP colorectal cancer",
    "colorectal_cancer",
    983,
    6701,
    EvaluationDesign("lodo", 8, 3, 1, 42, "outer_group"),
    "study_id",
)

lampp_ghs = _lampp(
    "lampp_ghs",
    "LAMPP general health status",
    "general_health_status",
    8033,
    9383,
    EvaluationDesign("lodo", 54, 3, 1, 42, "outer_group"),
    "study_id",
)

lampp_ibd = _lampp(
    "lampp_ibd",
    "LAMPP inflammatory bowel disease",
    "inflammatory_bowel_disease",
    1886,
    4411,
    EvaluationDesign("lodo", 2, 3, 1, 42, "subject"),
    "study_id",
)

lampp_dm7 = _lampp(
    "lampp_dm7",
    "LAMPP delivery mode ≤7 days",
    "delivery_mode",
    948,
    1958,
    EvaluationDesign("lodo", 2, 3, 1, 42, "subject"),
    "study_id",
)

lampp_dm90 = _lampp(
    "lampp_dm90",
    "LAMPP delivery mode ≤90 days",
    "delivery_mode",
    1461,
    2537,
    EvaluationDesign("lodo", 3, 3, 1, 42, "subject"),
    "study_id",
)


studies = (
    brown_mdd,
    prjna1190316,
    healthy_colombia,
    metaibs_ibs,
    prime_ptsd,
    lampp_scz,
    lampp_crc,
    lampp_ghs,
    lampp_ibd,
    lampp_dm7,
    lampp_dm90,
)
