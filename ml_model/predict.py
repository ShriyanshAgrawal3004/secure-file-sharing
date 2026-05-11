import pickle
from feature_extracter import extract_features

with open("/Users/shriyansh/Desktop/Project_Blockchain/New/secure-file-sharing/ml_model/model.pkl", "rb") as f:
    model = pickle.load(f)


def predict_algorithm(filepath, sensitivity):
    features = extract_features(filepath, sensitivity)
    return model.predict([features])[0]