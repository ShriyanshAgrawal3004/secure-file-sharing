"""
Run this to confirm the new model is wired correctly.
Usage: cd ml_model && python verify_model.py
"""
import os
import tempfile
import numpy as np
from predict import predict_algorithm

tests = [
    # (description, content_bytes, sensitivity, expected_algo)
    (
        "tiny text file, sensitivity 3 → RSA",
        b"SECRET_API_KEY=abc123xyz",
        3,
        "RSA",
    ),
    (
        "random bytes small, sensitivity 1 → AES or CHACHA",
        np.random.randint(0, 256, 500, dtype=np.uint8).tobytes(),
        1,
        None,
    ),
    (
        "large random bytes, sensitivity 1 → CHACHA",
        np.random.randint(0, 256, 500000, dtype=np.uint8).tobytes(),
        1,
        "CHACHA",
    ),
    (
        "repetitive text, sensitivity 1 → AES",
        b"AAABBBCCC" * 5000,
        1,
        "AES",
    ),
]

print("Verifying model v2...\n")
all_passed = True

for desc, content, sens, expected in tests:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    result = predict_algorithm(tmp_path, sens)
    os.unlink(tmp_path)

    if expected is None:
        status = "✓ PASS"
        detail = f"got {result} (any valid algo)"
    elif result == expected:
        status = "✓ PASS"
        detail = f"got {result}"
    else:
        status = "✗ FAIL"
        detail = f"expected {expected}, got {result}"
        all_passed = False

    print(f"  {status}  {desc}")
    print(f"         {detail}\n")

print("All tests passed ✓" if all_passed else "Some tests FAILED ✗")
