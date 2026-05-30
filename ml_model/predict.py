import pickle
import os
from feature_extracter import extract_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def predict_algorithm(filepath, sensitivity):
    features = extract_features(filepath, sensitivity)
    return model.predict([features])[0]