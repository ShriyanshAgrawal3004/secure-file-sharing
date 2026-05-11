import numpy as np
import os
import zlib

def calculate_entropy(data):
    if len(data) == 0:
        return 0
    probs = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256) / len(data)
    probs = probs[probs > 0]
    return -np.sum(probs * np.log2(probs))


def compression_ratio(data):
    compressed = zlib.compress(data)
    return len(compressed) / len(data)


def byte_distribution_std(data):
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    return np.std(counts)


def extract_features(filepath, sensitivity):
    with open(filepath, "rb") as f:
        data = f.read()

    size = len(data)
    entropy = calculate_entropy(data)
    comp_ratio = compression_ratio(data)
    byte_std = byte_distribution_std(data)

    return [
        size,
        entropy,
        comp_ratio,
        byte_std,
        sensitivity
    ]