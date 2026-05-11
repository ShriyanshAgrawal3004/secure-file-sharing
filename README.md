# Secure File Sharing (Blockchain + IPFS + ML Encryption)

## Overview
Secure File Sharing is a full-stack project that encrypts uploaded files, stores the encrypted payload in IPFS, and records the IPFS hash on-chain. A lightweight ML model selects the encryption algorithm based on file characteristics and a user-provided sensitivity level. The backend is built with Flask, smart contracts are written in Solidity, and the frontend is currently a minimal HTML form (intended to be replaced by a sophisticated UI).

## Why This Project Exists
Traditional file sharing lacks end-to-end privacy, auditability, and ownership control. This project aims to combine:
- **Encryption** (confidentiality)
- **IPFS** (content-addressed storage)
- **Blockchain** (immutable access & audit log)
- **ML-assisted decisions** (choosing encryption strategy per file)

## High-Level Architecture
1. **Client uploads file** with sensitivity level.
2. **ML model predicts algorithm** (AES / ChaCha / RSA planned).
3. **Backend encrypts file** and saves metadata locally.
4. **Encrypted file is uploaded to IPFS** via Pinata.
5. **IPFS hash is stored on-chain** in the FileStorage smart contract.

```
Frontend → Flask API → Encrypt → IPFS → Blockchain
```

## Key Features
- ML-driven algorithm selection
- AES/ChaCha encryption (RSA hybrid planned)
- IPFS upload via Pinata
- Solidity contract to store IPFS hashes and manage access
- Decrypt endpoint for local recovery

## Repository Structure
```
secure-file-sharing/
  backend/          # Flask API, crypto, IPFS, blockchain integrations
  blockchain/       # Solidity smart contract
  frontend/         # Current HTML form (placeholder)
  ml_model/         # Model training + feature extraction
  ipfs/             # Local IPFS artifacts (if any)
```

## Backend (Flask)
**Main file:** `backend/app.py`

### Endpoints
- `GET /` → health check
- `GET /upload` → simple HTML upload helper
- `POST /upload` → encrypts and stores file (IPFS + blockchain)
  - multipart fields: `file`, `sensitivity`
- `GET /decrypt/<filename>` → decrypts local encrypted file

### Example Response
```json
{
  "message": "File stored on blockchain",
  "ipfs_hash": "Qm...",
  "transaction_hash": "0x...",
  "algorithm": "AES"
}
```

## Blockchain (Solidity)
**Contract:** `blockchain/FileStorage.sol`

### What it stores
- IPFS hash per file
- Owner address
- Access control (grant/revoke)

### Contract functions
- `addFile(ipfsHash)`
- `grantAccess(fileId, user)`
- `revokeAccess(fileId, user)`
- `hasAccess(fileId, user)`
- `getFile(fileId)` (access-checked)

## IPFS (Pinata)
**Integration:** `backend/ipfs_utils.py`

The backend uploads encrypted files using Pinata’s `pinFileToIPFS` API. You must provide a valid key with pinning scopes.

### Required `.env` variables (backend)
```
PINATA_API_KEY=...
PINATA_SECRET_API_KEY=...
```

If you see `NO_SCOPES_FOUND`, your Pinata key doesn’t have pinning permissions.

## ML Model
**Core files:**
- `ml_model/predict.py` → loads `model.pkl` and predicts algorithm
- `ml_model/feature_extracter.py` → feature extraction
- `ml_model/train.py` → training scripts

The model takes file characteristics + sensitivity and predicts an algorithm. The backend currently encrypts with AES for any non-AES/CHACHA prediction (RSA hybrid is planned).

## Frontend Vision (Design Guide)
Below is the **full product vision** for a sophisticated UI. Use this as a spec for your final frontend build.

### 1) Product Goals
- Make encryption and storage feel **trusted, premium, and effortless**
- Clearly communicate **security state**, **ownership**, and **auditability**
- Give users confidence via **transparent progress + verification**

### 2) Pages & Navigation
**Core pages:**
- **Dashboard**: overview, recent uploads, chain status
- **Upload Flow**: file dropzone, sensitivity controls, preview, confirmation
- **File Vault**: searchable list of encrypted files
- **File Detail**: IPFS hash, algorithm, chain tx, permissions, download
- **Access Control**: grant/revoke access to other wallet addresses
- **Settings**: wallet config, IPFS provider settings, theme

### 3) Upload Experience (Ideal Flow)
1. Drag & drop file
2. Choose sensitivity with a slider + tooltip explanations
3. Preview file metadata (type, size, checksum)
4. “Encrypt & Store” stepper with live status:
   - encryption
   - IPFS pin
   - blockchain transaction
5. Success screen with:
   - algorithm used
   - IPFS hash
   - tx hash
   - “Copy link” buttons

### 4) Visual Style (Premium + Secure)
- **Theme:** dark background with soft gradients + neon accents
- **UI style:** glassmorphism panels with subtle shadows
- **Typography:** modern sans-serif (Inter / Manrope)
- **Color system:**
  - Primary: #6C5CE7 (purple)
  - Accent: #00D2D3 (cyan)
  - Success: #00C853
  - Warning: #FFB300
  - Danger: #FF5252

### 5) Components to Build
- File dropzone with animated state
- Encryption progress timeline
- IPFS + Blockchain badges
- “Security Score” widget
- Activity feed (who accessed what, when)
- File cards with hover actions
- Permissions modal + wallet address input

### 6) Micro-Interactions
- Animated upload progress (step-by-step)
- Pulsing status dots (connecting to IPFS/chain)
- Hover tooltips explaining AES/ChaCha
- “Copied” feedback for hashes

### 7) Empty + Error States
- Empty vault illustration (no files yet)
- Failed IPFS upload alert with retry
- Missing wallet/chain connection guidance

### 8) Responsive Layout
- Desktop: sidebar navigation + main panel
- Tablet/mobile: bottom nav + stacked cards
- Upload flow should be fully usable on mobile

### 9) Suggested Tech Stack
- **React + Vite** (fast dev + modern tooling)
- **Tailwind CSS** for rapid styling
- **Framer Motion** for animations
- **Wallet adapter** (if Ethereum wallet integration is added)

### 10) Frontend Data Model
At minimum, each file row should display:
- file name
- size
- upload timestamp
- algorithm
- IPFS hash
- blockchain tx hash
- access status

## Setup & Run
### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## How to Continue This Project (Developer Guide)
This section is a practical “handoff” guide for anyone cloning the repo and continuing development.

### Prerequisites
- **Python 3.10+** (project currently uses newer Python locally; any modern 3.x should work)
- **Ganache** (or any local Ethereum RPC) running at `http://127.0.0.1:7545`
- **Pinata account** (or alternative IPFS pinning provider)
- (Optional) Node.js + npm/pnpm if you rebuild the frontend with React/Vite

### First-run checklist (after cloning)
1. Create a virtual environment and install backend dependencies.
2. Create `backend/.env` (copy from an `.env.example` if provided).
3. Start Ganache and deploy the smart contract (then update contract address + ABI).
4. Run the Flask backend and test upload/decrypt.

### Environment variables (backend)
Create `backend/.env`:

```bash
# Pinata (required if you want IPFS pinning to work)
PINATA_API_KEY=...
PINATA_SECRET_API_KEY=...
```

If IPFS upload fails with `NO_SCOPES_FOUND`, create a new Pinata key that has **pinning scopes**.

### Running the backend on a different port
If port `5000` is already in use:

```bash
cd backend
PORT=5001 python app.py
```

### Where to implement new features
- **Upload / encryption pipeline:** `backend/app.py`
- **Encryption algorithms:** `backend/crypto_utils.py`
- **IPFS provider integration:** `backend/ipfs_utils.py`
- **Blockchain write operations:** `backend/blockchain_utils.py`
- **Contract config (address + ABI):** `backend/contract_config.py`
- **ML prediction (model inference):** `ml_model/predict.py`
- **Feature extraction:** `ml_model/feature_extracter.py`

### Smart contract workflow (when you redeploy)
If you redeploy `blockchain/FileStorage.sol`, you must update:
- `backend/contract_config.py` → `CONTRACT_ADDRESS`
- `backend/contract_config.py` → `ABI`

Also ensure Ganache RPC in `backend/blockchain_utils.py` matches your local chain:
- `ganache_url = "http://127.0.0.1:7545"`

### ML model workflow (retraining / improving predictions)
Current inference code loads a serialized model file and predicts an algorithm based on extracted features.

Typical improvement loop:
1. Add/clean training data in `ml_model/dataset.csv`.
2. Update or extend features in `ml_model/feature_extracter.py`.
3. Retrain with `ml_model/train.py` (or your training entrypoint).
4. Export/update `ml_model/model.pkl` used by `ml_model/predict.py`.
5. Verify uploads still work and the output algorithm set matches backend support.

Important: today the backend **actually encrypts** using only:
- `AES`
- `CHACHA`

If the model returns anything else (example: `RSA`), the backend currently falls back to AES.

### Frontend build plan (recommended)
The current `frontend/index.html` is just a placeholder form.

To build the “sophisticated” UI described above, create a separate frontend app that calls the Flask API:

Backend endpoints your UI will call:
- `POST /upload` (multipart form data: `file`, `sensitivity`)
- `GET /decrypt/<filename>` (download decrypted file)

Frontend implementation tips:
- Use a **multi-step/stepper UI** for encryption → IPFS → blockchain stages.
- Show **hash cards** (IPFS hash + transaction hash) with copy buttons.
- Include an “advanced” panel with raw JSON response for power users.

### Troubleshooting
**1) `POST /upload` returns an IPFS error**
- Check `backend/.env` keys are set.
- Fix Pinata key scopes (pinning permissions).
- Expect: encryption can still succeed even if IPFS fails.

**2) Blockchain write fails / web3 cannot connect**
- Confirm Ganache is running on `127.0.0.1:7545`.
- Confirm `CONTRACT_ADDRESS` is correct.
- Confirm ABI matches the deployed contract.

**3) Wrong algorithm naming**
- Backend expects `AES` and `CHACHA`.
- If your ML model returns `ChaCha20` or other labels, normalize them either in the model or in `backend/app.py` before encryption.

### Suggested Git workflow
- Do **not** commit secrets (`backend/.env`) or runtime outputs (`uploads/`, `encrypted/`, `decrypted/`).
- Add a `.gitignore` and commit `backend/.env.example` for safe onboarding.
- Use feature branches: `feat/frontend-dashboard`, `feat/ipfs-jwt`, etc.

### Environment Configuration
Create a `backend/.env` file with:
```bash
PINATA_API_KEY=...
PINATA_SECRET_API_KEY=...
```

### Local Blockchain
This project expects Ganache at:
```
http://127.0.0.1:7545
```
Update `backend/contract_config.py` if your contract address changes.

## Notes & Limitations
- RSA hybrid encryption is planned but not yet implemented.
- ML model is simple and can be replaced with a stronger classifier.
- IPFS upload requires valid Pinata scopes.

## Future Enhancements
- JWT-based Pinata auth support
- User auth + role-based access
- Full React UI with wallet integration
- Server-side audit logs
- Automated key rotation

---

If you want, I can also generate a **full frontend design system** (colors, tokens, layout, spacing, typography) or a **starter React UI scaffold** that matches this vision.
