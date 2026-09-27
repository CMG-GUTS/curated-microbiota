from curated_microbiota.collections import brown_mdd
from mllabiome import load_dataset

study = brown_mdd
dataset = load_dataset(study.mllabiome())

print(study.title)
print(f"Accession: {study.accession}")
print(f"Assay: {study.assay}")
print(f"Role: {study.role}")
print(f"Status: {study.status}")
print(f"Targets: {', '.join(study.targets)}")
print(f"Confounders: {', '.join(study.confounders) or 'none'}")
print(f"Samples: {len(dataset.sample_ids)}")
print(f"Features: {dataset.X_by_level['all'].shape[1]}")
print(f"Target: {dataset.target_name}")
print(f"Task: {dataset.task}")
print(f"Classes: {', '.join(dataset.class_labels) or 'n/a'}")
print(f"Counts: {study.counts}")
print(f"Metadata: {study.metadata}")
