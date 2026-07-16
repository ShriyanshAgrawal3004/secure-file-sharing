"""
model.py – model architecture / configuration reference.

The active model is a RandomForestClassifier trained in train.py and
persisted as model_v2.pkl.  This file documents the configuration so it
can be referenced without loading the pickle.
"""

from sklearn.ensemble import RandomForestClassifier

# Canonical model configuration – keep in sync with train.py
MODEL_CONFIG = dict(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

# Feature names in the exact order expected by the model
FEATURE_NAMES = [
    "entropy",
    "comp_ratio",
    "byte_std_norm",
    "size_bucket",
    "is_compressible",
    "high_entropy",
    "byte_uniformity",
    "unique_byte_ratio",
]

# Target classes
CLASSES = ["AES", "CHACHA", "RSA"]


def build_model() -> RandomForestClassifier:
    """Return a fresh (untrained) model instance with the canonical config."""
    return RandomForestClassifier(**MODEL_CONFIG)
