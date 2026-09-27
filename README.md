<p>
  <img
    src="https://raw.githubusercontent.com/CMG-GUTS/curated-microbiota/main/assets/favicon-curated-microbiota-oneline.svg"
    width="82"
    height="82"
    alt="mllabiome icon"
  >
  &nbsp;&nbsp;&nbsp;
  <a href="https://cmg-guts.github.io/mllabiome/">
    <img
      src="https://raw.githubusercontent.com/CMG-GUTS/curated-microbiota/main/assets/mllabiome-abundance-table.svg"
      width="350"
      align="right"
      alt="From microbiome abundance data through machine learning to learned patterns and interactions"
    >
  </a>
</p>
Versioned, analysis-ready microbiota cohorts and frozen benchmark partitions for the mllabiome ecosystem.

```python
from curated_microbiota.collections import brown_mdd

DATA = brown_mdd.mllabiome(target="mdd")
EVALUATION = brown_mdd.splits(target="mdd").mllabiome(
    optimize_metric="log_loss",
    n_jobs="auto",
)
```

Dataset payloads are retrieved lazily, verified against SHA-256 checksums, and cached locally. Benchmark-ready targets include immutable outer and inner evaluation assignments keyed by sample identifier.

## Installation

After the first GitHub release, the package can be installed directly from the tagged source release:

```bash
pip install "git+https://github.com/CMG-GUTS/curated-microbiota.git@v0.1.0"
```

For direct construction of mllabiome objects, install the optional integration dependencies:

```bash
pip install "curated-microbiota[mllabiome]"
```

The package code is lightweight. Dataset payloads and frozen split manifests are retrieved lazily from the `data-v0.1.0` GitHub Release and verified against registered SHA-256 checksums.

## Benchmark targets

`mllabiome-benchmark-v1` currently covers binary classification and regression. No multiclass benchmark target is included in the initial release. A cohort may contribute more than one benchmark problem: Brown MDD is used for both binary classification and regression, with a separate frozen split manifest for each target.

| Cohort | Target key | Data column | Benchmark use | Task | Outcome / classes | Internal validation | External evaluation |
|---|---|---|---|---|---|---|---|
| Brown MDD | `mdd` | `target_mdd` | Disease-status prediction | Binary classification | Control vs MDD; positive = MDD | 5 outer × 3 inner × 3 repeats | — |
| Brown MDD | `promis_depression` | `target_depression_severity` | Symptom-severity prediction | Regression | Continuous PROMIS depression severity | 5 outer × 3 inner × 3 repeats | — |
| PRJNA1190316 adolescent MDD | `mdd` | `target_mdd` | Disease-status prediction | Binary classification | Control vs MDD; positive = MDD | 5 outer × 3 inner × 3 repeats | — |
| PRIME PTSD prebiotic trial | `intervention` | `label` | Intervention-arm prediction in a longitudinal PTSD trial | Binary classification | Placebo vs prebiotic; positive = prebiotic | Subject-grouped 5 outer × 3 inner × 3 repeats; arm + time-point stratification | — |
| MetaIBS fecal IBS | `ibs` | `label` | Cross-study disease-status prediction | Binary classification | Healthy vs IBS; positive = IBS | LODO by source study; 3-fold study-grouped inner CV | — |
| LAMPP SCZ | `scz` | `label` | Schizophrenia phenotype prediction | Binary classification | LAMPP labels 0/1; positive = 1 | 5 outer × 3 inner × 3 repeats | LAMPP hidden-label test |
| LAMPP CRC | `crc` | `label` | Colorectal-cancer phenotype prediction | Binary classification | LAMPP labels 0/1; positive = 1 | LODO by source study; 3-fold study-grouped inner CV | LAMPP hidden-label test |
| LAMPP GHS | `ghs` | `label` | General-health-status prediction | Binary classification | LAMPP labels 0/1; positive = 1 | LODO by source study; 3-fold study-grouped inner CV | LAMPP hidden-label test |
| LAMPP IBD | `ibd` | `label` | Inflammatory-bowel-disease phenotype prediction | Binary classification | LAMPP labels 0/1; positive = 1 | LODO by source study; 3-fold subject-grouped inner CV | LAMPP hidden-label test |
| LAMPP DM7 | `dm7` | `label` | Delivery-mode prediction at ≤7 days | Binary classification | LAMPP labels 0/1; positive = 1 | LODO by source study; 3-fold subject-grouped inner CV | LAMPP hidden-label test |
| LAMPP DM90 | `dm90` | `label` | Delivery-mode prediction at ≤90 days | Binary classification | LAMPP labels 0/1; positive = 1 | LODO by source study; 3-fold subject-grouped inner CV | LAMPP hidden-label test |

Healthy Colombian men is distributed as a reference/domain-shift collection and does not have a supervised benchmark target.

The same target metadata are exposed programmatically:

```python
from curated_microbiota.collections import brown_mdd

brown_mdd.target("mdd").problem_type
# "binary_classification"

brown_mdd.target("promis_depression").problem_type
# "regression"
```

## Cohorts and sequencing

| Cohort | Source | Train N | Test N | Studies | Subjects | Specimen | Assay | Region / primers | Platform / instrument |
|---|---|---:|---:|---:|---:|---|---|---|---|
| Brown MDD | `PRJNA591924` | 90 | — | 1 | 90 | Stool | 16S rRNA amplicon | V4; 515F / 806R | Illumina MiSeq; 2×250 bp |
| PRJNA1190316 adolescent MDD | `PRJNA1190316` | 90 | — | 1 | 90 | Stool | 16S rRNA amplicon | V3–V4; 338F / 806R | Illumina NextSeq 2000; 2×300 bp |
| Healthy Colombian men | `PRJNA1000574` | 88 | — | 1 | 88 | Stool | 16S rRNA amplicon | V3–V4; Bakt_341F / Bakt_805R | Illumina MiSeq; 2×300 bp |
| PRIME PTSD prebiotic trial | PRIME / `PRJNA1086950` | 169 | — | 1 | 75 | Stool | 16S rRNA amplicon | V4; CS1_515F / CS2_806R | Illumina MiniSeq; 2×154 bp |
| MetaIBS fecal IBS | MetaIBS | 1,671 | — | 6 | 1,667 | Stool | 16S rRNA amplicon | Source-study dependent | Source-study dependent |
| LAMPP SCZ | LAMPP | 119 | 52 | 1 | 119 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |
| LAMPP CRC | LAMPP | 983 | 125 | 8 | 983 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |
| LAMPP GHS | LAMPP | 8,033 | 1,140 | 54 | 8,033 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |
| LAMPP IBD | LAMPP | 1,886 | 506 | 2 | 162 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |
| LAMPP DM7 | LAMPP | 948 | 188 | 2 | 649 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |
| LAMPP DM90 | LAMPP | 1,461 | 101 | 3 | 751 | Gut metagenome | Shotgun metagenomics | — | Source-study dependent |

Healthy Colombian men corresponds to BioProject `PRJNA1000574`; the paired neuroimaging dataset is OpenNeuro `ds004648`.

## PRIME PTSD longitudinal benchmark

The `prime_ptsd` collection is derived from the SILVA observed-abundance download from PRIME for BioProject `PRJNA1086950`. PRIME processed the public 16S reads through its standardized DADA2/QIIME 2 pipeline and SILVA 138.2 taxonomy. The packaged table contains 169 stool samples from 75 participant identifiers collected at baseline, 2 weeks, and/or 12 weeks.

All participants are annotated with PTSD. The supervised target is therefore not PTSD diagnosis; it is randomized intervention arm, with prebiotic encoded as the positive class and placebo as the negative class. The original publication reports 70 participants in the final clinical analysis, whereas the public PRIME/SRA-derived sequencing subset contains 75 participant identifiers. curated-microbiota preserves the public PRIME sample set rather than attempting to reconstruct an unverified clinical-analysis subset.

Because participants contribute repeated longitudinal specimens, the benchmark uses subject-grouped repeated nested cross-validation. No participant can occur in both train and test or inner train and validation partitions. The frozen folds additionally stratify on treatment arm and collection time point to stabilize the longitudinal composition across folds. The design is 5 outer folds, 3 inner folds, and 3 repeats.

```python
from curated_microbiota.collections import prime_ptsd

DATA = prime_ptsd.mllabiome()
EVALUATION = prime_ptsd.splits().mllabiome(
    optimize_metric="log_loss",
    n_jobs="auto",
)
```

PRIME should be cited independently: Zhang Z, Zhao H, Wang T. *PRIME: a database for 16S rRNA microbiome data with phenotypic reference and comprehensive metadata*. Nucleic Acids Research. DOI: `10.1093/nar/gkaf1057`. The underlying trial is Voigt RM et al. *Prebiotics as an adjunct therapy for posttraumatic stress disorder: a pilot randomized controlled trial*. Frontiers in Neuroscience. DOI: `10.3389/fnins.2024.1477519`.

## MetaIBS fecal IBS benchmark

The `metaibs_ibs` collection is derived from the MetaIBS aggregated taxonomic tables and metadata for six case-control studies. The analytical cohort is restricted to metadata rows explicitly annotated as stool. The packaged abundance matrix is physically restricted to those sample identifiers before study matrices are aligned, so non-fecal or otherwise excluded source samples cannot enter mllabiome implicitly.

| Source study | Country | Packaged N | Healthy | IBS | Region / primers | Sequencing platform |
|---|---|---:|---:|---:|---|---|
| AGP-2021 | United States | 1,183 | 594 | 589 | V4; 515F / 806R | Illumina MiSeq |
| Fukui-2020 | Japan | 110 | 26 | 84 | V1-V2; 27F / 338R | Illumina MiSeq |
| Hugerth-2019 | Sweden | 174 | 130 | 44 | V3-V4; 341F / 805R | Illumina MiSeq |
| Liu-2020 | China | 128 | 44 | 84 | V3-V4; 338F / 806R | Illumina MiSeq |
| LoPresti-2019 | Italy | 46 | 27 | 19 | V1-V3; 28F / 519R | 454 GS Junior |
| Nagel-2016 | Australia | 30 | 15 | 15 | V4; 515F / 806R | Ion Torrent PGM |

The benchmark target is IBS versus healthy control. Outer evaluation is six-fold leave-one-dataset-out, with one complete source study held out per fold. The corresponding inner model-selection assignments are 3-fold study-grouped splits across the remaining source studies. This also keeps the known repeated Hugerth subject identifiers within a single inner partition. The distributed split manifest fixes both outer and inner assignments.

MetaIBS should be cited independently:

Carcy S, Ostner J, Tran V, Menden MP, Müller CL. *MetaIBS: large-scale amplicon-based meta analysis of irritable bowel syndrome*. bioRxiv. DOI: `10.1101/2024.01.22.575775`. Source repository: `https://github.com/bio-datascience/MetaIBS`.


## mllabiome benchmark

`mllabiome-benchmark-v1` is the benchmark family used for the mllabiome manuscript. The benchmark identifier is shared across datasets while the evaluation design is target-specific.

Single-study classification targets use three repetitions of 5-fold outer nested cross-validation with 3-fold inner cross-validation. The PRIME PTSD intervention target is longitudinal and therefore uses subject-grouped outer and inner folds, with treatment arm plus collection time point used for stratification. Regression targets use the corresponding shuffled K-fold design. Repeated observations are kept within subject whenever subject grouping is required.

Multi-study benchmark targets use leave-one-dataset-out evaluation. The MetaIBS IBS target uses source study as the outer dataset and 3-fold study-grouped inner model selection. Multi-study LAMPP tasks use leave-one-dataset-out evaluation, with `study_id` defining the outer held-out dataset. CRC and GHS use 3-fold study-grouped inner model selection because subjects are unique. IBD, DM7, and DM90 use 3-fold subject-grouped inner model selection because subjects contribute repeated observations. The complete outer and inner assignments are distributed with each target and are not regenerated during manuscript analyses.

The split-manifest schema fingerprints sample identifiers, targets, outer dataset assignments, subject identities, and the evaluation design. mllabiome verifies the manifest against the loaded analytical cohort before fitting models.

For GHS, some source studies contain only one class. Such studies remain valid LODO test domains, but fold-specific AUROC is undefined for those domains. Pooled LODO out-of-dataset predictions remain available for metrics that require both classes. Task-level QC is distributed in each LAMPP asset.

```python
from curated_microbiota.collections import lampp_ibd

DATA = lampp_ibd.mllabiome()
EVALUATION = lampp_ibd.splits().mllabiome(
    optimize_metric="log_loss",
    n_jobs="auto",
)
INFERENCE = lampp_ibd.external_test.inference(
    targets=("mpma_b", "mpma_e"),
)
```

After the mllabiome inference stage writes `inference/predictions.tsv`, an official two-column LAMPP submission can be exported deterministically from the positive-class probability:

```python
SUBMISSION = lampp_ibd.external_test.submission(
    "runs/LAMPP-IBD/inference/predictions.tsv",
    strategy="mpma_b",
)
```

The LAMPP test labels are not included in curated-microbiota. The external-test object is inference-only; predictions are evaluated through the official LAMPP benchmark.

## LAMPP

LAMPP (Live Assessment of Metagenomics-based tools for host Phenotype Prediction) is an external benchmark for host-phenotype prediction from gut shotgun metagenomic data. curated-microbiota provides mllabiome-aligned training profiles, metadata, immutable within-training evaluation manifests, and the corresponding hidden-label test inputs.

The LAMPP benchmark and datasets should be cited independently from mllabiome:

Barak N, Bhattacharya H, Asnicar F, Sung J, Segata N, Yassour M. *LAMPP: A benchmark for continuous evaluation of host phenotype prediction from shotgun metagenomic data*. bioRxiv. DOI: `10.1101/2025.06.12.658885`. Official benchmark: `https://lampp.yassourlab.com/`.

Model and MPMA selection must use only the labeled LAMPP training data and the published mllabiome split manifests. Hidden-label test predictions are generated only after selection and final refitting on the complete labeled training set.

## Collections API

```python
from curated_microbiota import collections

collections.available()
collections.available(status="ready")
collections.available(benchmark=True)
collections.available(assay="shotgun_metagenomics")
collections.metaibs_ibs.splits()

study = collections.lampp_crc
print(study.source)
print(study.targets)
print(study.splits().design)
print(study.external_test.labels_available)
```

## Retrieval

Accessing a study file, creating an `mllabiome.Data` object, resolving a benchmark split set, or resolving a LAMPP external test downloads only the selected study archive. Every archive and extracted file is verified against the checksums registered by the Python package.

The default source is the `curated-microbiota/collections` GitHub Release `data-v0.5.0`. `CURATED_MICROBIOTA_RELEASE_URL` and `CURATED_MICROBIOTA_CACHE` can override the release source and cache location.
