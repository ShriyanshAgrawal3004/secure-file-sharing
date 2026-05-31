import numpy as np
import zlib


def calculate_entropy(data: bytes) -> float:
    if len(data) == 0:
        return 0.0
    probs = np.bincount(
        np.frombuffer(data, dtype=np.uint8), minlength=256
    ) / len(data)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def extract_features(filepath: str, sensitivity=None) -> list:
    """
    Extract 8 features from a file.
    sensitivity parameter kept for backward compatibility but NOT used.
    Returns list of 8 floats in this exact order:
    [entropy, comp_ratio, byte_std_norm, size_bucket,
     is_compressible, high_entropy, byte_uniformity, unique_byte_ratio]
    """
    with open(filepath, "rb") as f:
        data = f.read()

    size = len(data)
    if size == 0:
        return [0.0] * 8

    entropy = calculate_entropy(data)

    compressed = zlib.compress(data)
    comp_ratio = len(compressed) / size

    byte_counts = np.bincount(
        np.frombuffer(data, dtype=np.uint8), minlength=256
    )
    byte_std = float(np.std(byte_counts))
    byte_std_norm = byte_std / (size / 256)

    is_compressible = 1 if comp_ratio < 0.85 else 0
    high_entropy = 1 if entropy > 7.2 else 0
    byte_uniformity = max(0.0, 1.0 - (byte_std / 128.0))
    unique_byte_ratio = len(set(data)) / 256.0

    if size < 1024:
        size_bucket = 0
    elif size < 102400:
        size_bucket = 1
    elif size < 10485760:
        size_bucket = 2
    else:
        size_bucket = 3

    return [
        entropy,
        comp_ratio,
        byte_std_norm,
        size_bucket,
        is_compressible,
        high_entropy,
        byte_uniformity,
        unique_byte_ratio,
    ]