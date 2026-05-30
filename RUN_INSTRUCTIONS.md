# Cold Vault - Project Startup Guide

## Prerequisites

- **macOS** (or Linux with similar commands)
- **Node.js 16+** (for React frontend)
- **Python 3.9+** (for Flask backend)
- **Ganache** (Ethereum test network - download from https://trufflesuite.com/ganache/)
- **Git**

---

## Step 1: Start Ganache (Blockchain Network)

1. **Open Ganache** (if not already running)
   - Click "Quick Start" or create a workspace
   - Ganache runs on `http://127.0.0.1:7545` by default
   - **Copy a wallet address** from the Accounts tab (you'll need this for testing)

2. **Verify Ganache is running:**
   ```bash
   curl http://127.0.0.1:7545
   # Should return 404 (that's OK, Ganache is running)
   ```

---

## Step 2: Deploy Smart Contract to Ganache

1. **Deploy the contract (recommended automatic way):**

   ```bash
   cd /Users/aamiribrahim/secure-file-sharing/backend
   python3 deploy_contract.py
   ```

   This will:
   - compile `blockchain/FileAccess.sol`
   - deploy it to Ganache
   - update `backend/contract_config.py` with the new address

   **Important:** Ganache resets the chain when restarted. If you restart Ganache,
   run `python3 deploy_contract.py` again so the backend points to the new contract.

2. **Verify contract deployment:**

   ```bash
   curl http://127.0.0.1:5000/blockchain/health
   ```

   Look for: `"has_code": true`

### If Ganache is restarted

Ganache resets the chain when restarted. Re-deploy the contract with:

```bash
cd /Users/aamiribrahim/secure-file-sharing/backend
python3 deploy_contract.py
```

### Optional: Bundle all uncommitted changes into a new branch

If you want all current local changes bundled into a new branch, tell me and I’ll:

- create a new branch
- add all modified/new files
- commit them
- push the branch to origin

---

## Step 3: Start Backend (Flask API)

1. **Open a NEW terminal and navigate to backend:**

   ```bash
   cd /Users/aamiribrahim/secure-file-sharing/backend
   ```

2. **Install dependencies (first time only):**

   ```bash
   pip3 install -r requirements.txt
   ```

3. **Start Flask server:**

   ```bash
   python3 app.py
   ```

4. **Expected output:**

   ```
   * Serving Flask app 'app'
   * Debug mode: on
   * Running on http://127.0.0.1:5000
   ```

5. **Keep this terminal open** (don't close it)

### If port 5000 is in use:

```bash
# Kill process using port 5000
lsof -i :5000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Then restart Flask
python3 app.py
```

---

## Step 4: Start Frontend (React + Vite)

1. **Open a NEW terminal and navigate to frontend:**

   ```bash
   cd /Users/aamiribrahim/secure-file-sharing/frontend
   ```

2. **Install dependencies (first time only):**

   ```bash
   npm install
   ```

3. **Start development server:**

   ```bash
   npm run dev
   ```

4. **Expected output:**

   ```
   VITE v5.4.21 ready in 196 ms

   ➜  Local:   http://127.0.0.1:5174/
   ➜  press h to show help
   ```

5. **Keep this terminal open** (don't close it)

---

## Step 5: Access the App

1. **Open browser:** http://127.0.0.1:5174
2. **You'll see a login page**
3. **Paste your Ganache wallet address** (from Step 1)
4. **Click "CONNECT ->"**
5. **You're logged in!** ✅

---

## Step 6: Use the System

### Upload a File:

1. Click **"Upload"** in the sidebar
2. **Drop a file** or select one
3. **Set sensitivity** (HIGH/MEDIUM/LOW)
4. Click **"ENCRYPT & STORE"**
5. File is encrypted, stored locally, and recorded on blockchain

### View Your Files:

- Click **"My Vault"** to see all your uploaded files

### Share with Others:

1. Click **"My Vault"**
2. Find file → Click **"Manage Access"**
3. Enter another wallet address
4. Click **"Grant Access"**

### Request Access (as different user):

1. **Logout** (click LOGOUT button)
2. **Login with a different Ganache wallet**
3. Click **"My Requests"**
4. Find file → Click **"Request Access"**
5. Original owner will see it in their "My Requests" tab

### Download File:

1. Go to **"My Vault"** or **"Shared Files"**
2. Click **"Download"** on any file you have access to
3. File is automatically decrypted and downloaded

---

## Troubleshooting

### "Network Error" when logging in:

- **Solution:** Backend not running
- Check: Is Flask running on http://127.0.0.1:5000?
- Command: `python3 app.py` in `/backend` folder

### "Access denied" / Blockchain actions fail:

- **Cause:** Contract not deployed to the current Ganache instance
- **Fix:** Re-deploy and update contract address:

   ```bash
   cd /Users/aamiribrahim/secure-file-sharing/backend
   python3 deploy_contract.py
   ```

   Then verify:

   ```bash
   curl http://127.0.0.1:5000/blockchain/health
   ```

   Look for: `"has_code": true`

### Port 5000 already in use:

```bash
# Kill the process
lsof -i :5000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Restart Flask
python3 app.py
```

### Port 5174 already in use:

```bash
# Kill the process on port 5174
lsof -i :5174 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Restart Vite
npm run dev
```

### "Cannot connect to blockchain":

- **Solution:** Ganache not running
- Start Ganache: Open app and click "Quick Start"
- Verify: http://127.0.0.1:7545 should respond

### "Invalid wallet address":

- **Solution:** Paste a valid Ganache wallet address
- Copy from Ganache app → Accounts tab
- Starts with `0x` followed by 40 hex characters

### CORS Error in browser console:

- **Solution:** Already fixed! Backend now allows port 5174
- If error persists: Restart Flask backend

---

## File Structure

```
/secure-file-sharing
├── backend/
│   ├── app.py                    # Flask API (main)
│   ├── requirements.txt          # Python dependencies
│   ├── contract_config.py        # Blockchain contract config
│   ├── blockchain_utils.py       # Web3 contract functions
│   ├── crypto_utils.py           # AES & ChaCha encryption
│   ├── ipfs_utils.py            # IPFS upload (optional)
│   ├── database.py              # SQLAlchemy models
│   ├── uploads/                 # Incoming files
│   ├── encrypted/               # Encrypted files
│   ├── decrypted/               # Downloaded files
│   └── vault.db                 # SQLite database
├── frontend/
│   ├── package.json             # NPM dependencies
│   ├── vite.config.js           # Vite config
│   ├── src/
│   │   ├── App.jsx              # Main component
│   │   ├── main.jsx             # Entry point
│   │   ├── pages/               # Page components
│   │   │   ├── Upload.jsx
│   │   │   ├── Vault.jsx
│   │   │   └── ...
│   │   └── components/          # UI components
│   └── index.html               # HTML template
└── blockchain/
    ├── FileAccess.sol           # Smart contract
    └── FileStorage.sol          # Storage contract
```

---

## Environment Variables

Backend needs a `.env` file in `/backend`:

```env
SECRET_KEY=dev-cold-vault-secret
GANACHE_URL=http://127.0.0.1:7545
PINATA_API_KEY=your-pinata-key (optional)
PINATA_API_SECRET=your-pinata-secret (optional)
DEFAULT_OWNER_ADDRESS=0x... (optional)
```

---

## Quick Terminal Commands Reference

```bash
# Start everything from scratch (3 terminals):

# Terminal 1: Start Ganache
# (Open Ganache app manually)

# Terminal 2: Backend
cd /Users/aamiribrahim/secure-file-sharing/backend
python3 app.py

# Terminal 3: Frontend
cd /Users/aamiribrahim/secure-file-sharing/frontend
npm run dev

# Then open browser:
# http://127.0.0.1:5174
```

---

## Testing with curl

```bash
# Login
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"0x742d35Cc6634C0532925a3b844Bc9e7595f42bE"}'

# Check blockchain health
curl http://127.0.0.1:5000/blockchain/health

# Get your files
curl http://127.0.0.1:5000/user/0x742d35Cc6634C0532925a3b844Bc9e7595f42bE/files

# Request access to file
curl -X POST http://127.0.0.1:5000/request_access \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "user_address": "0xUserWallet..."
  }'

# Grant access (as owner)
curl -X POST http://127.0.0.1:5000/grant_access \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "owner_address": "0xOwnerWallet...",
    "user_address": "0xUserWallet..."
  }'
```

---

## How It Works (Architecture)

1. **User Login**: Wallet address → Session stored → User record in DB
2. **Upload File**:
   - ML model predicts encryption algorithm (AES or ChaCha)
   - File encrypted locally
   - Encrypted file stored on server
   - Metadata (file_id, IPFS hash) stored on Ganache blockchain
3. **Access Control**:
   - Owner stores file on blockchain with contract.storeFile()
   - Other users request access → recorded in DB
   - Owner approves/denies → contract.grantAccess() executed
   - Download checks blockchain: has access? → Yes: decrypt & send, No: 403 Forbidden
4. **Download**:
   - Check blockchain for access permission
   - If allowed: retrieve encrypted file, decrypt, send to user
   - If denied: return "Access Denied"

---

## Notes

- All wallets are **Ganache test accounts** (fake ETH, for testing only)
- Files are **encrypted before upload** (AES or ChaCha20 based on ML prediction)
- **No passwords needed** - wallet address is the authentication
- **Access control is on blockchain** - immutable, transparent, verifiable
- **IPFS upload is optional** - system works without Pinata API key

---

✅ **You're all set! Happy file sharing!** 🚀
