# ML Model Analysis: 22 Questions Answered

## 1. What exact type of model and training approach?
**RandomForestClassifier** from scikit-learn with **100 estimators** (decision trees). Training code in `ml_model/train.py` (lines 10-18): reads dataset.csv, drops "algo" column for features (X), uses "algo" as target (y), applies 80-20 train-test split via `train_test_split(X, y, test_size=0.2)`, fits the model, and saves with pickle.

## 2. What are the input features (full extraction code)?
Five features extracted in `ml_model/feature_extracter.py` (lines 24-35):
- **size**: file size in bytes
- **entropy**: Shannon entropy via `calculate_entropy(data)` (lines 4-8)
- **comp_ratio**: zlib compression ratio (line 34)
- **byte_std**: standard deviation of byte distribution (line 35)
- **sensitivity**: user-provided sensitivity level (1-3)

### Feature Extraction Code:
```python
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
```

## 3. What are the output labels/classes?
**Three classes**: `['AES', 'CHACHA', 'RSA']` (verified from model.classes_)

## 4. Training data: first 10 rows, total count, generation method, columns?

### Dataset Statistics:
- **Total rows**: 388 (387 data rows + 1 header)
- **Columns**: `size, entropy, compression, byte_std, sensitivity, algo`

### First 10 Data Rows:
```
size,entropy,compression,byte_std,sensitivity,algo
75546,7.571575245923906,0.758941572022344,476.7801730725163,1,CHACHA
75546,7.571575245923906,0.758941572022344,476.7801730725163,2,CHACHA
75546,7.571575245923906,0.758941572022344,476.7801730725163,3,CHACHA
4343713,7.9800474943145705,0.9376590948803477,3111.3660759195755,1,CHACHA
4343713,7.9800474943145705,0.9376590948803477,3111.3660759195755,2,CHACHA
4343713,7.9800474943145705,0.9376590948803477,3111.3660759195755,3,CHACHA
91824,7.822638229630232,0.8642402857640704,247.5710362072874,1,CHACHA
91824,7.822638229630232,0.8642402857640704,247.5710362072874,2,CHACHA
91824,7.822638229630232,0.8642402857640704,247.5710362072874,3,CHACHA
2683,6.058730728927168,0.6306373462541931,22.498602590611565,1,AES
```

### Generation Method:
`ml_model/create_dataset.py` (lines 1-30):
- Reads actual sample files from "sample_files" folder
- Extracts features for each file across 3 sensitivity levels
- Applies heuristic labeling (lines 17-23):
  - If entropy > 7.5 → CHACHA
  - Else if sensitivity == 3 → RSA
  - Else → AES

## 5. Preprocessing code?
`ml_model/train.py` (lines 10-14): Minimal preprocessing—reads CSV, drops "algo" column for X (features), uses "algo" as y (labels), applies train-test split. **No scaling, normalization, or feature engineering applied.**

```python
df = pd.read_csv("dataset.csv")
X = df.drop("algo", axis=1)
y = df["algo"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

## 6. Model accuracy and validation approach?
`ml_model/train.py` (lines 19-24):
- Uses **80-20 test split** with `train_test_split()` (no stratification)
- Prints `accuracy_score(y_test, preds)`
- Prints confusion matrix and classification report
- **Exact accuracy value is not saved**—only printed during training
- Model file is 209KB (model.pkl)

```python
preds = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, preds))
print("Confusion Matrix:")
print(confusion_matrix(y_test, preds))
print("\nClassification Report:")
print(classification_report(y_test, preds))
```

## 7. Full predict.py function analysis?
`ml_model/predict.py`:

```python
import pickle
import os
from feature_extracter import extract_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_algorithm(filepath, sensitivity):
    features = extract_features(filepath, sensitivity)
    return model.predict([features])[0]
```

- Loads model.pkl into global `model` variable (lines 5-7)
- `predict_algorithm(filepath, sensitivity)` function (lines 11-12):
  - Calls `extract_features(filepath, sensitivity)` (returns list of 5 values)
  - Returns `model.predict([features])[0]` — single string prediction from first (only) sample

## 8. Model return type?
**String**: Returns single class name (`'AES'`, `'CHACHA'`, or `'RSA'`)—not probability, not array.

## 9. Each current feature analysis: measurement, usefulness, correctness, type, range?

| Feature | Measurement | Type | Range | Usefulness | Correctness |
|---------|------------|------|-------|-----------|------------|
| **size** | File size in bytes | int | 66–4,343,713 bytes | Low—compression ratio and entropy already encode size info; redundant | ✓ Correct |
| **entropy** | Shannon entropy: -∑p(x)log₂p(x) | float | ~4.99–7.99 nats | High—distinguishes random (high) from structured (low) data | ✓ Correct (np.bincount + log2) |
| **compression** | Compressed size / original size | float | 0.63–1.09 | High—high values = incompressible/random = use CHACHA | ✓ Correct (zlib.compress) |
| **byte_std** | Std dev of byte frequency distribution | float | 0.73–3,111.36 | Medium—similar to entropy but less standard; redundant | ✓ Correct (np.std) |
| **sensitivity** | User-provided 1-3 level | int | 1, 2, 3 | Low—model treats as feature, but should be policy input | ✗ Wrong placement (categorical policy flag, not data property) |

## 10. Wrong, redundant, or misleading features?
1. **sensitivity**: Policy input (1-3), not data property. Should not be ML feature—should directly map to algorithm via policy rules, not trained prediction.
2. **size + byte_std redundant**: Byte_std scales with file size; entropy and compression already capture content properties.
3. **byte_std vs entropy**: Both measure randomness; entropy is standard statistical measure; byte_std is custom and less interpretable.

## 11. Entropy calculation code (if exists)?
`ml_model/feature_extracter.py` (lines 4-8):

```python
def calculate_entropy(data):
    if len(data) == 0:
        return 0
    probs = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256) / len(data)
    probs = probs[probs > 0]
    return -np.sum(probs * np.log2(probs))
```

Correctly implements Shannon entropy: counts byte frequencies (0-255), normalizes to probabilities, filters zeros, sums -p log₂ p.

## 12. How is file size feature used?
Raw file size in bytes added to feature vector. **Not normalized** relative to other samples. Random Forest can handle raw magnitudes, but size and byte_std are correlated (larger files = larger byte_std typically). Contributes to overfitting on file size rather than content properties.

## 13. How is sensitivity feature used?
`ml_model/create_dataset.py` (lines 9-10): For each file, features extracted 3 times (sensitivity=1, 2, 3). **Same file features → different labels based on sensitivity**. Example: 2683 bytes, entropy 6.06 → (sens=1: AES, sens=2: AES, sens=3: RSA). Model learns sensitivity→algorithm mapping (not ideal—should be policy rule, not ML prediction).

## 14. What algorithm targets (unique label values) does model support?
**Three targets**: `AES`, `CHACHA`, `RSA` (from model.classes_)

## 15. Does the model predict RSA? How is it handled in backend?
**Yes, model predicts RSA**, but `backend/app.py` has **no RSA implementation**:

```python
if algo == "AES":
    enc_data = encrypt_aes(data)
elif algo in {"CHACHA", "CHACHA20", "CHACHA-20"}:
    algo = "CHACHA"
    enc_data = encrypt_chacha(data)
else:
    algo = "AES"
    enc_data = encrypt_aes(data)  # ← RSA silently falls through to AES
```

## 16. Fallback code for unsupported algorithms?
`backend/app.py` (lines 339-340):
```python
else:
    algo = "AES"
    enc_data = encrypt_aes(data)
```
No error logging, no user notification—silently converts RSA predictions to AES.

## 17. Dataset balance (class distribution)?
**Highly imbalanced**:
- CHACHA: 315 (81.1%)
- AES: 48 (12.4%)
- RSA: 24 (6.2%)

Random Forest **not sensitive to class imbalance** like logistic regression, but RSA is severely underrepresented. Model may rarely predict RSA.

## 18. Data quality issues?
1. **Synthetic labeling**: Not real-world labels—heuristic rules in `create_dataset.py` applied, not actual security requirements
2. **Repeated samples**: Each unique (size, entropy, compression, byte_std) tuple labeled 3 times with different sensitivities → artificial data inflation
3. **No ground truth**: No verification that entropy > 7.5 truly requires CHACHA; heuristic assumptions unvalidated
4. **Sensitivity leakage**: Sensitivity (user policy input) used as feature, not label driver
5. **Limited file diversity**: Only sample_files folder; likely small dataset

## 19. Dataset generation method: real vs synthetic?
**Semi-synthetic**: Real files read from `ml_model/create_dataset.py` (lines 9-10) from "sample_files" folder, but **labels are synthetic heuristics** (not true encryption requirements). Features computed from real file content; labels generated by rules, not ground truth.

## 20. Biggest model weakness?
**Sensitivity-driven overfitting**: Same file byte-content mapped to 3 different algorithms based only on sensitivity value. Model learns sensitivity→algo mapping instead of file-content→algo mapping. Example: 66-byte file labeled AES(sens=1), AES(sens=2), RSA(sens=3). When predicting, model will nearly always output based on sensitivity input, not file analysis. **Fundamentally, this is not an ML problem—it's a policy lookup.**

## 21. Missing elements for proper AES/ChaCha20/RSA selection?
1. **RSA implementation**: `backend/crypto_utils.py` has NO RSA encrypt/decrypt functions
2. **Real labels**: Ground truth encryption requirements (not heuristics)
3. **Use-case features**: Payload size, latency requirements, security level (RSA for key exchange, not bulk data)
4. **Performance metrics**: Training data lacks crypto context—should include: key exchange overhead, throughput, FIPS compliance flags
5. **Policy rules**: Sensitivity should map directly to algo via policy, not ML prediction
6. **Validation approach**: Train/test split should not contaminate features with sensitivity—stratify by real use case

## 22. RSA support requirements in crypto_utils.py?
`backend/crypto_utils.py` **currently imports**: 
```python
from Crypto.Cipher import AES, ChaCha20
from Crypto.Random import get_random_bytes
```

**To support RSA, requires**:
```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
```

**New functions needed**:
- `encrypt_rsa(file_data, public_key)` 
- `decrypt_rsa(enc_data, private_key)`
- Key generation and storage logic
- Backend API changes to handle RSA public/private key pairs

**Current status**: **0 lines of RSA code exist**

---

## Summary
Model is production-incomplete. RSA predictions silently fail to AES. Sensitivity should not be an ML feature. Dataset is synthetically labeled heuristics on real files. Model trains to predict sensitivity→algo, not file-content→algo. The system needs policy-based algorithm selection, not ML prediction.

## Recommendations
1. Remove sensitivity from ML features—use for policy-based routing instead
2. Implement RSA support in crypto_utils.py or disable RSA predictions
3. Collect real ground-truth labels for algorithm selection
4. Use only file-content features (entropy, compression, byte_std)
5. Consider if ML is needed at all—policy rules may be sufficient
