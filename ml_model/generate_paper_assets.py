import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
from sklearn.preprocessing import label_binarize
import os

# --- Journal Formatting Setup ---
# Standard double-column IEEE/ACM width is usually 3.5 inches, full width is ~7.16 inches.
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'figure.dpi': 300
})

ASSET_DIR = "paper_assets"
os.makedirs(ASSET_DIR, exist_ok=True)

# ==========================================
# 1. ML Model Evaluation Figures & Tables
# ==========================================
df = pd.read_csv("dataset.csv")

X = df.drop("algo", axis=1)
y = df["algo"]
classes = ['AES', 'CHACHA', 'RSA']
y_bin = label_binarize(y, classes=classes)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
_, _, y_train_bin, y_test_bin = train_test_split(X, y_bin, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)
y_score = model.predict_proba(X_test)

# Figure 5a: Confusion Matrix
plt.figure(figsize=(4, 3.5))
cm = confusion_matrix(y_test, preds, labels=classes)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
plt.title('Confusion Matrix')
plt.ylabel('True Algorithm')
plt.xlabel('Predicted Algorithm')
plt.tight_layout()
plt.savefig(f"{ASSET_DIR}/Fig5a_Confusion_Matrix.pdf", format='pdf', bbox_inches='tight')
plt.close()

# Figure 5b: ROC Curve (Multiclass OVR)
plt.figure(figsize=(5, 4))
colors = ['blue', 'red', 'green']
for i, color in zip(range(len(classes)), colors):
    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, color=color, lw=2, label=f'ROC {classes[i]} (area = {roc_auc:.2f})')

plt.plot([0, 1], [0, 1], 'k--', lw=2)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(f"{ASSET_DIR}/Fig5b_ROC_Curve.pdf", format='pdf', bbox_inches='tight')
plt.close()

# Table 1: Dataset Description
desc_df = df.describe().transpose()
desc_df.to_latex(f"{ASSET_DIR}/Table1_Dataset_Description.tex", float_format="%.2f")

# Table 3: ML Performance Metrics
report = classification_report(y_test, preds, output_dict=True)
report_df = pd.DataFrame(report).transpose()
report_df.to_latex(f"{ASSET_DIR}/Table3_ML_Metrics.tex", float_format="%.3f")

# ==========================================
# 2. Performance & Cryptographic Data (MOCKUP)
# ==========================================
# Figure 4: Encryption Performance Scalability
# NOTE: Replace 'file_sizes' and 'times' with your actual empirical benchmark logs.
file_sizes_mb = np.array([1, 5, 10, 50, 100])
aes_times = np.array([0.05, 0.22, 0.45, 2.1, 4.3])
chacha_times = np.array([0.03, 0.15, 0.30, 1.4, 2.8])

plt.figure(figsize=(5, 4))
plt.plot(file_sizes_mb, aes_times, marker='o', label='AES-256')
plt.plot(file_sizes_mb, chacha_times, marker='s', label='ChaCha20')
plt.xlabel('File Size (MB)')
plt.ylabel('Encryption Time (Seconds)')
plt.title('Cryptographic Scalability')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.savefig(f"{ASSET_DIR}/Fig4_Crypto_Performance.pdf", format='pdf', bbox_inches='tight')
plt.close()

# Table 2: Smart Contract Gas Consumption (MOCKUP)
# NOTE: Replace with actual Ganache/Hardhat gas logs.
gas_data = {
    "Function": ["storeFile", "requestAccess", "grantAccess", "hasAccess", "getFile"],
    "Gas Used": [112450, 45210, 52300, 24100, 26000],
    "Est. USD Cost (At 20 Gwei)": [0.45, 0.18, 0.21, 0.10, 0.10]
}
gas_df = pd.DataFrame(gas_data)
gas_df.to_latex(f"{ASSET_DIR}/Table2_Gas_Costs.tex", index=False)

print(f"All assets successfully generated in the '{ASSET_DIR}' directory.")