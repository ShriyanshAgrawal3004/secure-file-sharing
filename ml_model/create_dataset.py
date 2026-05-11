import os
import pandas as pd
from feature_extracter import extract_features

DATASET = []

folder = "sample_files"

for file in os.listdir(folder):
    path = os.path.join(folder, file)

    # Simulate sensitivity levels
    for sensitivity in [1, 2, 3]:
        features = extract_features(path, sensitivity)

        # Labeling logic (semi-realistic)
        size = features[0]
        entropy = features[1]

        if entropy > 7.5:
            algo = "CHACHA"
        elif sensitivity == 3:
            algo = "RSA"
        else:
            algo = "AES"

        DATASET.append(features + [algo])

df = pd.DataFrame(DATASET, columns=[
    "size", "entropy", "compression", "byte_std", "sensitivity", "algo"
])

df.to_csv("dataset.csv", index=False)

print("Dataset created!")