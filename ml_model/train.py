"""
Train a RandomForestClassifier on dataset_v2.csv (8-feature set) and save
the fitted model + scaler as model_v2.pkl and scaler.pkl.

Features (in order, as produced by feature_extracter.extract_features):
  0  entropy
  1  comp_ratio
  2  byte_std_norm
  3  size_bucket
  4  is_compressible
  5  high_entropy
  6  byte_uniformity
  7  unique_byte_ratio

Labels: AES | CHACHA | RSA
"""

import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

FEATURE_COLS = [
    "entropy",
    "comp_ratio",
    "byte_std_norm",
    "size_bucket",
    "is_compressible",
    "high_entropy",
    "byte_uniformity",
    "unique_byte_ratio",
]

df = pd.read_csv("dataset_v2.csv")

# Validate expected columns are present
missing = [c for c in FEATURE_COLS + ["algo"] if c not in df.columns]
if missing:
    raise ValueError(f"dataset_v2.csv is missing columns: {missing}")

X = df[FEATURE_COLS].values
y = df["algo"].values

# Train / test split (stratified to keep class balance)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale features – helps with byte_std_norm which can be on a very different
# scale from the binary flag features.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# RandomForest – 200 estimators, balanced class weights to handle any skew
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train_scaled, y_train)

preds = model.predict(X_test_scaled)

print(f"Accuracy : {accuracy_score(y_test, preds):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, preds))
print("Confusion Matrix:")
print(confusion_matrix(y_test, preds))

# Feature importances
importances = sorted(
    zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]
)
print("\nFeature Importances:")
for name, imp in importances:
    print(f"  {name:<20} {imp:.4f}")

# Persist
with open("model_v2.pkl", "wb") as f:
    pickle.dump(model, f)

with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("\nSaved model_v2.pkl and scaler.pkl")
