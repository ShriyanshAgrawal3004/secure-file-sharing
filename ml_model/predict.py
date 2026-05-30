import pickle
import os
from feature_extracter import extract_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_v2.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)


def predict_algorithm(filepath: str, sensitivity) -> str:
    """
    Predict encryption algorithm for a file.

    sensitivity is a POLICY OVERRIDE, not an ML feature:
      - sensitivity=3 AND file < 100KB AND low entropy → always RSA
      - otherwise → use ML model prediction

    Returns: "AES", "CHACHA", or "RSA"
    """
    file_size = os.path.getsize(filepath)

    # Policy override: critical small files always get RSA
    if int(sensitivity) == 3 and file_size < 102400:
        features = extract_features(filepath)
        entropy = features[0]
        if entropy < 7.0:
            return "RSA"

    features = extract_features(filepath)
    scaled = scaler.transform([features])
    prediction = model.predict(scaled)[0]
    return str(prediction)