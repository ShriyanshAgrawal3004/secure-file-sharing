"""
predict.py – load the trained RandomForest model and recommend an encryption
algorithm for a given file.

Algorithm mapping produced by the model:
  AES    – moderate entropy, compressible, low/medium sensitivity
  CHACHA – high entropy, incompressible, low/medium sensitivity
  RSA    – small / text-like files, high sensitivity (model learns this from
           the training data labeling rules in create_dataset.py)
"""

import pickle
import os
from feature_extracter import extract_features

_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_DIR, "model_v2.pkl")
SCALER_PATH = os.path.join(_DIR, "scaler.pkl")

# ---------------------------------------------------------------------------
# Load model and scaler; fall back to a simple rule-based predictor if the
# pickle files are absent (e.g. first clone, CI environment).
# ---------------------------------------------------------------------------
try:
    with open(MODEL_PATH, "rb") as f:
        _model = pickle.load(f)

    with open(SCALER_PATH, "rb") as f:
        _scaler = pickle.load(f)

    _MODEL_AVAILABLE = True

except FileNotFoundError:
    _MODEL_AVAILABLE = False

    class _DummyScaler:
        def transform(self, X):
            return X

    class _DummyModel:
        def predict(self, X):
            return ["AES"] * len(X)

    _model = _DummyModel()
    _scaler = _DummyScaler()


def _rule_based_fallback(entropy: float, comp_ratio: float, sensitivity: int) -> str:
    """Simple heuristic used when the trained model is unavailable."""
    if sensitivity >= 3:
        return "RSA"
    if entropy > 7.2:
        return "CHACHA"
    return "AES"


def predict_algorithm(filepath: str, sensitivity) -> str:
    """
    Predict the best encryption algorithm for *filepath* given its *sensitivity*.

    Parameters
    ----------
    filepath    : path to the file to analyse
    sensitivity : int-like, 0 = LOW … 3 = CRITICAL

    Returns
    -------
    One of "AES", "CHACHA", "RSA"
    """
    try:
        sens_level = int(sensitivity)
    except (ValueError, TypeError):
        sens_level = 1  # default: MEDIUM

    # Extract the 8 features that the model was trained on.
    # extract_features returns:
    #   [entropy, comp_ratio, byte_std_norm, size_bucket,
    #    is_compressible, high_entropy, byte_uniformity, unique_byte_ratio]
    features = extract_features(filepath, sensitivity)

    if not _MODEL_AVAILABLE:
        entropy, comp_ratio = features[0], features[1]
        return _rule_based_fallback(entropy, comp_ratio, sens_level)

    # Scale and predict
    features_scaled = _scaler.transform([features])
    prediction = _model.predict(features_scaled)[0]

    # Post-processing: override with RSA for CRITICAL sensitivity regardless
    # of what the model predicts, since RSA provides asymmetric key-based
    # security required for critical data.
    if sens_level >= 3:
        return "RSA"

    return str(prediction)
