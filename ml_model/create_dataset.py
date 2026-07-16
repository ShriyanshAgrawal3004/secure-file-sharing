"""
create_dataset.py – generate dataset_v2.csv from files in the sample_files/
directory.

Feature order produced by extract_features (feature_extracter.py):
  0  entropy
  1  comp_ratio
  2  byte_std_norm
  3  size_bucket
  4  is_compressible
  5  high_entropy
  6  byte_uniformity
  7  unique_byte_ratio

Labeling rules (semi-realistic):
  - High-entropy, incompressible data → CHACHA (fast stream cipher, ideal for
    already-compressed/encrypted content)
  - Low-entropy, compressible data + HIGH sensitivity (3) → RSA (asymmetric,
    maximum security for small structured files)
  - Everything else → AES (strong symmetric cipher, good all-rounder)

The dataset is augmented across three sensitivity levels (1, 2, 3) so the
model can learn how sensitivity interacts with file characteristics.
"""

import os
import pandas as pd
from feature_extracter import extract_features

DATASET = []
COLUMNS = [
    "entropy",
    "comp_ratio",
    "byte_std_norm",
    "size_bucket",
    "is_compressible",
    "high_entropy",
    "byte_uniformity",
    "unique_byte_ratio",
    "algo",
]

SAMPLE_DIR = "sample_files"

if not os.path.isdir(SAMPLE_DIR):
    raise FileNotFoundError(
        f"Directory '{SAMPLE_DIR}' not found. "
        "Place representative files there before running this script."
    )

for filename in os.listdir(SAMPLE_DIR):
    path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.isfile(path):
        continue

    for sensitivity in [1, 2, 3]:
        features = extract_features(path, sensitivity)

        # Unpack named indices for readability
        entropy         = features[0]
        comp_ratio      = features[1]
        high_entropy_f  = features[5]   # binary flag: entropy > 7.2
        is_compressible = features[4]   # binary flag: comp_ratio < 0.85

        # Labeling logic
        if high_entropy_f and not is_compressible:
            # Already-random / compressed data → stream cipher
            algo = "CHACHA"
        elif sensitivity == 3:
            # Critical sensitivity, structured/low-entropy file → asymmetric
            algo = "RSA"
        else:
            # Default: strong symmetric cipher
            algo = "AES"

        DATASET.append(features + [algo])

df = pd.DataFrame(DATASET, columns=COLUMNS)
df.to_csv("dataset_v2.csv", index=False)

print(f"Dataset created: {len(df)} rows → dataset_v2.csv")
print(df["algo"].value_counts().to_string())
