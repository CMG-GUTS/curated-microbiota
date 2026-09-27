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
    version="0.1.0",
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
    _asset='brown_mdd-0.1.0.tar.gz',
    _asset_sha256='ee07a1f5c2fecc29e85e31ada1f13741c348003f75fd40760b853fe683d7c360',
    _files=_files({
        'counts.tsv': '47231f116ba2561bc57ca1f24e862fad34992b2e12d01752bfbf9a35c8cbec85',
        'feature_metadata.tsv': 'e9d376217b5bfd4ab2ab2e3c141551df80c30881eb70aaa186ed7a20f5cce9eb',
        'metadata.tsv': '3c7f96a12a93ddb1767d5999e3d42909843c291172e52aaa8d6f5d42651b8205',
        'provenance.yaml': 'f0894330ac9e23a3c3f612fa7eccd0a57af1ffeb8386c2e6b730888837bb497e',
        'qc.tsv': '700938b1f2ecadc6417bf6ff34e14ddd3c1dcb1221cde6ceeb814e53282f7e93',
        'splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv': '5a2f4b08b5bb0bc60dbc376ad61bd0e77a18e98b4085afb15b124562b65de1b9',
        'splits/promis_depression/mllabiome-benchmark-v1/cv_splits.tsv': '741e624068c575b0246b92c6acc7d57772fc51f14a7357991c86c0d9b472a082',
    }),
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
    version="0.1.0",
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
    _asset='prjna1190316-0.1.0.tar.gz',
    _asset_sha256='32a79ccf2a20d9e266c2de03db0d65226477792bb411bb7531bc4360f55fcec4',
    _files=_files({
        'counts.tsv': '53ea60ceff098b513880d220a3a924c54fc5a6bf73e8e2f293d95b0c607515b9',
        'feature_metadata.tsv': 'c4c6cc9d6e2fcd041ff85ae72ded07cc67ce004a9ae7a8307b7b6c43a757df95',
        'metadata.tsv': '93ea12836a23f1ee05911522797a119fc7f84b970d015ecf264edaa8836ec599',
        'provenance.yaml': '0f74739c7f04fada5431c4655d15a51097ee3f6af71a900083f5e3b483972b57',
        'qc.tsv': 'e099bfb06df1403f5fa5d1d5904e1e1e2461d47102f2f0501a612930242c306a',
        'splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv': 'e324c9b829771fea51264602e359f05739f543b8ba9ce4dacbece837014d9181',
    }),
    _targets=(_Target("mdd", "target_mdd", "classification", 1, ("control", "mdd"), ((0, 0), (1, 1))),),
    _splits=(_Split("mdd", MLLABIOME_BENCHMARK, MLLABIOME_NCV, "splits/mdd/mllabiome-benchmark-v1/cv_splits.tsv"),),
    _default="mdd",
    _subject="sample_id",
)


healthy_colombia = Study(
    name="healthy_colombia",
    title="Healthy Colombian men",
    version="0.1.0",
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
    _asset='healthy_colombia-0.1.0.tar.gz',
    _asset_sha256='afa92cc2ae37f5ac5389442a818c7d250783b1af840c688f396a4b097b1691a8',
    _files=_files({
        'counts.tsv': 'f0502601dbda96d93a16769889546dc6f40c6d6626558107e54656ca432879ca',
        'feature_metadata.tsv': 'da5e1d7042e7faf2218ebefe20d8d43df666b4c40065cfce465bf3509518c324',
        'metadata.tsv': 'f6a5d6d3bff8abc850a85a4cc2ea6824da7879f8a4a25b3e7ef333c65ae33250',
        'provenance.yaml': '7d91fde0728742ce2e4d4e177bc777ffbd214fbc8042d8568c51227808e4582d',
        'qc.tsv': '123d0842bd9af916998209d0b45bc580f4957c9f80e6cc96c935f3696d104206',
    }),
)


def _lampp(
    name: str,
    title: str,
    condition: str,
    samples: int,
    features: int,
    asset: str,
    asset_sha256: str,
    files: dict[str, str],
    design: EvaluationDesign,
    group: str | None,
) -> Study:
    task = name.removeprefix("lampp_")
    return Study(
        name=name,
        title=title,
        version="0.1.0",
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
        _asset=asset,
        _asset_sha256=asset_sha256,
        _files=_files(files),
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
    version="0.1.0",
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
    _asset="metaibs_ibs-0.1.0.tar.gz",
    _asset_sha256="a2bd7a11483e9352e354e5038bf6c9b1e76737f7e8d42e183419e895c8e797d4",
    _files=_files({'metadata.tsv': '0c11384ac94202b2a8778a4aa8bba248c38bf5863051888832e1df0514328d7d', 'profiles.tsv': '3b7d401254d67d3228c1ddf2e2ff20fd2dc1a3efa7d4b43d24c871cf8951ec5d', 'provenance.yaml': '61443d89460599afa81e3e57332ace109c1ec8c5a944c26515d5d5c7e87239e5', 'qc.tsv': '70ecd8846a0e5c97df9ee227f48ae665bd66b3380a9d36c0e3f68157735210a1', 'splits/ibs/mllabiome-benchmark-v1/cv_splits.tsv': '71c9cbb71179b01ffb63d4db69301331a616afa1a40794adf7c36e7dad9e00c8', 'study_metadata.tsv': '197ccf568307a7e9fcee027101b56414c18ed81d27e85632cb41badd50519699'}),
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
    version="0.1.0",
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
    _asset="prime_ptsd-0.1.0.tar.gz",
    _asset_sha256="c9f5145fb1ad42f986659660573b26b811014284f4ce9075bba0857a753116a2",
    _files=_files({
        'metadata.tsv': '37d30a3143279151c8a91d53911ba1651e7f1e576978cd6d1a26573373df7865',
        'profiles.tsv': 'aff91fd0b59550c5b51739b02bbd193be9667fde31eaca2c087171d8d2ccb2af',
        'source_metadata.tsv': '4a657fc76e4f8c526019baf109ddbc6ea73a735663c132da24a289e41466fde3',
        'qc.tsv': 'a73d02f4e4e8d9b45a68ad2817344740cc10e645cf4ac0c11416c4041df81c73',
        'provenance.yaml': '7dca900b73d34acc29a4bd4f28c046347170894590576be301789ba0466ef8e1',
        'splits/intervention/mllabiome-benchmark-v1/cv_splits.tsv': '0f86d3e3bbb92701a255706ac8361ac946563e170ff7353eaeffc364f785bea6'
}),
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
    'lampp_scz-0.1.0.tar.gz',
    '17ebde24e9e93f510b7727d49d0cca211405a18a5680f542c8628cee0a4906fb',
    {'metadata.tsv': '9e579f2eea79e9fc52e7ab009c432c7e0be66792c0031c01e5789ccc1f8aa896', 'profiles.tsv': '4fa8dcd837362616b0b151b76af61f9d54e26f7c081ca238cbe1168d3481e5c2', 'provenance.yaml': '35567e006638051661fd29d1b7e67ffa11a79d6d9980d7803b7646f1fcb4ebc3', 'qc.tsv': '8391976a1268218f1006526ef31d092843d3be042b1c364f8bb3f20826d8ef37', 'splits/scz/mllabiome-benchmark-v1/cv_splits.tsv': '892d1c1b2bafe3a2e2d52cf156e3aa13932f9721b3f1d893119bf8f4a925760f', 'test_metadata.tsv': 'b9f1e482944381ed9de713000865e6b18a303a69645a963c0f3832e29ab15008', 'test_profiles.tsv': 'e410ed588bbebc029c8db89d5c892a06ef26bf55c2fde590878689fd1a7962d9'},
    MLLABIOME_NCV,
    None,
)

lampp_crc = _lampp(
    "lampp_crc",
    "LAMPP colorectal cancer",
    "colorectal_cancer",
    983,
    6701,
    'lampp_crc-0.1.0.tar.gz',
    'b54fc7d13fbd00da78b702fb82ee28d6137f04d06ae99e3e4c86dadc3ec75439',
    {'metadata.tsv': '1c2a9e46d34b244de6b94d2df8bf10b19b15a6fa564546fbf09d9b3982a9e332', 'profiles.tsv': 'd11caf5efd0bf0697c4edb0285bdd5f00101682edd056d3ed3ee2b45db3f3516', 'provenance.yaml': '6cd7fcb85a64b3a6c1fd39df7eea04b774d4f7753f40c7215b7a085a94f542be', 'qc.tsv': 'd9e98e243a12951b0d8672e2792bc6648451129ac9ac165416eccb7f70abc8df', 'splits/crc/mllabiome-benchmark-v1/cv_splits.tsv': '7d7d58b3886617fd87c012f9b1f35e615470db1df44087eba8361a2c826428a3', 'test_metadata.tsv': 'bfb31095453cacc6e713926ffa6a9cad0a1970f2c6e1e3013227f60a502b102c', 'test_profiles.tsv': '5c328e117320b71656199ac81f1020ce9614a9588c83155ab138a425c802713c'},
    EvaluationDesign("lodo", 8, 3, 1, 42, "outer_group"),
    "study_id",
)

lampp_ghs = _lampp(
    "lampp_ghs",
    "LAMPP general health status",
    "general_health_status",
    8033,
    9383,
    'lampp_ghs-0.1.0.tar.gz',
    '55f18e061c7c857923d8f793759e6347244a45fb281bfb6f0387039fd9a8e65f',
    {'metadata.tsv': 'dfedd81e2f1c8b1c3ebc382f19ae5feeaf2113009db5eaccdb1e29d7970aedcd', 'profiles.tsv': 'e3851c3b86aab5e9f72f06ea25699bbbb41f96a8f047c852cc0f6df31f08fa7e', 'provenance.yaml': 'c140605f37e38467c7dd92d54109b748589a9291da75ddfea7dabfe3a830b958', 'qc.tsv': '596e6aac98a5758096375de53fad879a5c0a51461e79b14b0bfd0db56600a10f', 'splits/ghs/mllabiome-benchmark-v1/cv_splits.tsv': '44e7f887d68f6e1f3dcf6104d44f45fd6b071a0b2ff024b659d5cac5b566db96', 'test_metadata.tsv': '4ab4944658f1a2eb3443f394f4e47cf65f829d185626ae482b8647aeb57edfa9', 'test_profiles.tsv': '083cc93aa41eebcc3a6f2f0b5b571d1e6513434aedda3a44db22f92f8ade898e'},
    EvaluationDesign("lodo", 54, 3, 1, 42, "outer_group"),
    "study_id",
)

lampp_ibd = _lampp(
    "lampp_ibd",
    "LAMPP inflammatory bowel disease",
    "inflammatory_bowel_disease",
    1886,
    4411,
    'lampp_ibd-0.1.0.tar.gz',
    '29231f925fd141197fcb73de7e3faee3b5c0eaa20cf44c6dac27774b3ea530fa',
    {'metadata.tsv': 'a46e4af720a103295a29574e573367d5b4c36ccaf6088879dc11fe9cad3ee128', 'profiles.tsv': '2ad55c5caec9ecdff2c898c597d64efde8911ebdca94b0e21ed6ac33837d6a0b', 'provenance.yaml': '79682f97b115ed06cfbc80a352bf33a1aac4de6f9d5c7026587617c2216bc29f', 'qc.tsv': 'bb0ec292af76d13bbcc2cb9ecd8bd914b09ccecea5abe1e61080f70ea7af4e03', 'splits/ibd/mllabiome-benchmark-v1/cv_splits.tsv': 'efe70ebd92cfe88ca1f3ddb50177e9af10cb2888e955caae095b997dd949f5b3', 'test_metadata.tsv': '0a25b9037428e2921c81c0000e86b21c8bc318b7e773364c53b748f9ce08762a', 'test_profiles.tsv': '293c6010c2247e9ba86e0d94426f2d5b3b8f5f7aa5a5fd5040dab5e8892d465c'},
    EvaluationDesign("lodo", 2, 3, 1, 42, "subject"),
    "study_id",
)

lampp_dm7 = _lampp(
    "lampp_dm7",
    "LAMPP delivery mode ≤7 days",
    "delivery_mode",
    948,
    1958,
    'lampp_dm7-0.1.0.tar.gz',
    'f851a5974171a32af98d9e65f9ea06a2c068fd6689d83d6ee06d23665e990eeb',
    {'metadata.tsv': 'e360fb43d7354b62af541af490ba5b67db2ce9c6f311e84fc30cfd850470e13b', 'profiles.tsv': '2dd37a5924e3ac50659e09acfaa99c50aaa7c3bbdd72b5d96fe8f70e79ca80ea', 'provenance.yaml': 'a86f1fc1ea68439e4b69144a8f68ad1726d1fdab291560ad9ed6a79fe1baffa5', 'qc.tsv': 'c80b4e60fbceb94b6384097f4f46db50d5549ed3447530668586a9e5bf63bf10', 'splits/dm7/mllabiome-benchmark-v1/cv_splits.tsv': '72dbced1680efb4c61fb86db514574856ded44dde6a04c6b6e12b7155a9a114c', 'test_metadata.tsv': '1009caa112266e45656ab915d60efa4f85fab7ec8410f9a4238d58549aecbbc4', 'test_profiles.tsv': '20d3f1dea917d7f838245c023fa21badd284b1f78754015f9f5aba15dfc8c221'},
    EvaluationDesign("lodo", 2, 3, 1, 42, "subject"),
    "study_id",
)

lampp_dm90 = _lampp(
    "lampp_dm90",
    "LAMPP delivery mode ≤90 days",
    "delivery_mode",
    1461,
    2537,
    'lampp_dm90-0.1.0.tar.gz',
    'edf0ae3140e633eb5cc5bfb782b56f28b04da77c8405cffe49c8fa78e650a988',
    {'metadata.tsv': 'c78e8a31f23ddf9c3119d38f0eebc4c3c22772570c033a150c1b0858f928fb25', 'profiles.tsv': '15050c82db9d2041a282c7f8ca82fcee3e2168ffdf20c5ec5c18f3a6b50f869c', 'provenance.yaml': '0bdc96db8bac704ad1a9bb5fce42f9b10a881bb54a968b972c831ffff79e9726', 'qc.tsv': '37548ebe67073fb512df1afe6ff2ccbd32643e8676fa04db60e12ace548ab697', 'splits/dm90/mllabiome-benchmark-v1/cv_splits.tsv': '779f1b5f9e42f9cd0a95c2b4c1451b2b5fbc5cb5a2d96f07f77f1b5c8ed58ef4', 'test_metadata.tsv': '93b7903c60465a0a95567bbbc7f209e6894436051ff9cda8b11af933199cf246', 'test_profiles.tsv': '92c88de13187b48b24f1bf23fdfefcaba3413df5ac62c1ba015e15eb867af9b9'},
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
