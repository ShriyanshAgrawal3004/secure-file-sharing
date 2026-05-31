# Secure File Sharing - Complete Codebase Analysis

**Analysis Date:** May 30, 2026

---

## Table of Contents

1. [Current Role System](#current-role-system)
2. [Access Control Logic](#access-control-logic)
3. [Profile / Account System](#profile--account-system)
4. [File Ownership](#file-ownership)
5. [Frontend Problems](#frontend-problems)
6. [What Needs to Be Built](#what-needs-to-be-built)
7. [Summary](#summary)

---

## CURRENT ROLE SYSTEM

### Question 1: Are there any roles defined anywhere?

**Answer:** Yes.

In [`blockchain/FileStorage.sol`](blockchain/FileStorage.sol), there is an enum for roles:

```solidity
// blockchain/FileStorage.sol, lines 6–6
enum Role { NONE, VIEWER, ADMIN }
```

There is also a per-file role mapping:

```solidity
// blockchain/FileStorage.sol, lines 17–18
// fileId → user → role
mapping(uint => mapping(address => Role)) public roles;
```

Additionally, "owner" is stored in file structs in both contracts:

```solidity
// blockchain/FileAccess.sol, lines 7–11
struct FileData {
    uint256 id;
    string ipfsHash;
    address owner;
}
```

```solidity
// blockchain/FileStorage.sol, lines 8–11
struct File {
    string ipfsHash;
    address owner;
}
```

---

### Question 2: In the smart contract, who can call grantAccess and revokeAccess? Is there any require() or modifier that restricts these to the file owner only?

**Answer:** Both are owner-only.

In [`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), **grantAccess** is owner-only:

```solidity
// blockchain/FileAccess.sol, lines 50–58
function grantAccess(uint256 fileId, address user) public {
    require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
    require(msg.sender == files[fileId].owner, "Only owner");
    require(user != address(0), "Invalid user");

    permissions[fileId][user] = true;
    emit AccessGranted(fileId, msg.sender, user);
}
```

**Note:** `FileAccess.sol` has **no revokeAccess** function.

In [`blockchain/FileStorage.sol`](blockchain/FileStorage.sol), both **grantAccess** and **revokeAccess** are owner-only:

```solidity
// blockchain/FileStorage.sol, lines 38–45
function grantAccess(uint fileId, address user, Role role) public {
    require(msg.sender == files[fileId].owner, "Not owner");
    require(accessRequests[fileId][user], "No request");

    roles[fileId][user] = role;
    accessRequests[fileId][user] = false;
}
```

```solidity
// blockchain/FileStorage.sol, lines 47–52
function revokeAccess(uint fileId, address user) public {
    require(msg.sender == files[fileId].owner, "Not owner");

    roles[fileId][user] = Role.NONE;
}
```

---

### Question 3: Right now, can ANY address grant themselves access to ANY file? Walk through the exact code path that would allow or prevent this.

**Answer:** No. Prevented by contract checks.

The call path in the backend:

1. [`backend/app.py`](backend/app.py) `/grant_access` route calls `grant_access(...)`  
   (lines 310–323)

2. [`backend/blockchain_utils.py`](backend/blockchain_utils.py) `grant_access()` sends the transaction  
   (lines 63–70):

   ```python
   tx = contract.functions.grantAccess(int(file_id), user).transact({"from": owner})
   ```

3. Contract enforces owner-only restriction  
   ([`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), lines 52–54):
   ```solidity
   require(msg.sender == files[fileId].owner, "Only owner");
   ```

**Key Point:** The transaction must be sent **from the owner address** to succeed. Any other address will fail the `require` statement.

---

### Question 4: Is there any concept of "requesting access" in the contract or backend? (pending state, event, mapping of requests) — show the code or say no.

**Answer:** Yes. Present in **both contracts** and the backend.

In [`blockchain/FileAccess.sol`](blockchain/FileAccess.sol):

```solidity
// blockchain/FileAccess.sol, lines 35–47
function requestAccess(uint256 fileId) public {
    require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
    require(msg.sender != files[fileId].owner, "Owner has access");

    // Prevent duplicate requests
    address[] storage reqs = accessRequests[fileId];
    for (uint256 i = 0; i < reqs.length; i++) {
        require(reqs[i] != msg.sender, "Already requested");
    }

    reqs.push(msg.sender);
    emit AccessRequested(fileId, msg.sender);
}
```

```solidity
// blockchain/FileAccess.sol, line 17
mapping(uint256 => address[]) public accessRequests;
```

In [`blockchain/FileStorage.sol`](blockchain/FileStorage.sol):

```solidity
// blockchain/FileStorage.sol, lines 20–21
mapping(uint => mapping(address => bool)) public accessRequests;
```

```solidity
// blockchain/FileStorage.sol, lines 33–35
function requestAccess(uint fileId) public {
    accessRequests[fileId][msg.sender] = true;
}
```

Backend route in [`backend/app.py`](backend/app.py):

```python
# backend/app.py, lines 295–307
@app.route("/request_access", methods=["POST"])
def request_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    user_address = data.get("user_address")

    if file_id is None or not user_address:
        return {"error": "Required JSON fields: file_id, user_address"}, 400

    try:
        tx_hash = request_access(int(file_id), user_address)
        return {"message": "Access requested", "transaction_hash": tx_hash}
    except Exception as e:
        return {"error": str(e)}, 403
```

---

## ACCESS CONTROL LOGIC

### Question 5: Show the exact hasAccess() function from the contract. Who has access by default — only the owner, or everyone?

**Answer:** Only the owner has default access.

```solidity
// blockchain/FileAccess.sol, lines 60–66
function hasAccess(uint256 fileId, address user) public view returns (bool) {
    require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
    if (user == files[fileId].owner) {
        return true;
    }
    return permissions[fileId][user];
}
```

**Default Access:** By default, **only the owner** can access a file. Anyone else must have an explicit entry in the `permissions` mapping.

---

### Question 6: If User A uploads a file and User B wants to download it: What exact steps would need to happen in the current code for that to work? Is any of that actually implemented or is it all missing?

**Answer:** The access-control flow is **implemented in backend/contract but NOT wired to frontend**.

#### User A Uploads (Implemented)

In [`backend/app.py`](backend/app.py), lines 175–233:

```python
owner_address = request.form.get("owner_address") or os.environ.get("DEFAULT_OWNER_ADDRESS")
# ... file processing ...
blockchain_data = store_file(ipfs_hash, owner_address)
```

In [`backend/blockchain_utils.py`](backend/blockchain_utils.py), lines 39–51:

```python
def store_file(ipfs_hash: str, owner_address: str) -> Dict[str, Any]:
    """Store a file hash on-chain. Returns {tx_hash, file_id}."""
    # ...
    tx = contract.functions.storeFile(ipfs_hash).transact({"from": owner})
    # ...
    return {"tx_hash": tx.hex(), "file_id": int(file_id)}
```

Contract stores owner in [`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), line 30:

```solidity
files[fileId] = FileData({id: fileId, ipfsHash: ipfsHash, owner: msg.sender});
```

#### User B Requests Access (Implemented in Backend, NOT in Frontend)

Backend route exists in [`backend/app.py`](backend/app.py), lines 295–307:

```python
@app.route("/request_access", methods=["POST"])
def request_access_api():
    # ... takes file_id and user_address ...
    tx_hash = request_access(int(file_id), user_address)
```

#### Owner Grants Access (Implemented in Backend, NOT in Frontend)

Backend route exists in [`backend/app.py`](backend/app.py), lines 310–323:

```python
@app.route("/grant_access", methods=["POST"])
def grant_access_api():
    # ... takes file_id, owner_address, user_address ...
    tx_hash = grant_access(int(file_id), owner_address, user_address)
```

#### User B Downloads (Implemented in Backend, NOT in Frontend)

Backend route exists in [`backend/app.py`](backend/app.py), lines 326–342:

```python
@app.route("/get_file/<int:file_id>", methods=["GET"])
def get_file_api(file_id):
    user_address = request.args.get("user_address")
    # ... checks has_access ...
    ipfs_hash = get_file(int(file_id), user_address)
    return {"ipfs_hash": ipfs_hash}
```

#### What is Missing

**The frontend does NOT call these routes.** Instead:

The frontend "download" link uses local decryption:

[`frontend/src/components/FileTable.jsx`](frontend/src/components/FileTable.jsx), lines 46–47:

```jsx
<a
  className="amber-button px-3 py-2 text-[11px]"
  href={`http://127.0.0.1:5000/decrypt/${file.name}`}
>
  DOWNLOAD
</a>
```

This calls `/decrypt/<filename>` which **does not check access control**:

[`backend/app.py`](backend/app.py), lines 269–293:

```python
@app.route("/decrypt/<filename>", methods=["GET"])
def decrypt_file(filename):
    # No access checks — just decrypts and returns file
```

---

### Question 7: Is grantAccess called anywhere in the backend (app.py or any route)? Show the route or confirm it is not wired up.

**Answer:** Yes, it is wired in backend.

[`backend/app.py`](backend/app.py), lines 310–323:

```python
@app.route("/grant_access", methods=["POST"])
def grant_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    owner_address = data.get("owner_address")
    user_address = data.get("user_address")

    if file_id is None or not owner_address or not user_address:
        return {"error": "Required JSON fields: file_id, owner_address, user_address"}, 400

    try:
        tx_hash = grant_access(int(file_id), owner_address, user_address)
        return {"message": "Access granted", "transaction_hash": tx_hash}
    except Exception as e:
        return {"error": str(e)}, 403
```

**However, this route is NOT called from the frontend.**

---

### Question 8: Is revokeAccess called anywhere in the backend? Show the route or confirm it is missing.

**Answer:** Missing.

There is **no** `revoke_access` route in [`backend/app.py`](backend/app.py).

Additionally, the active ABI in [`backend/contract_config.py`](backend/contract_config.py) is for `FileAccess.sol`, which has **no** `revokeAccess` function.

The alternative contract `FileStorage.sol` **does** have `revokeAccess`, but it is not deployed or used in the backend.

---

## PROFILE / ACCOUNT SYSTEM

### Question 9: Is there any concept of a user profile or account anywhere in the codebase?

**Answer:** No.

There are:

- No user tables
- No database
- No sessions
- No wallet-to-profile mappings
- No authentication logic

---

### Question 10: When a file is uploaded, is the uploader's identity stored anywhere? (wallet address, user ID, IP, session token — anything) Show exactly where and how, or confirm it is not stored.

**Answer:** Yes, **on-chain only**.

The owner is stored in the file struct on the blockchain:

[`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), line 30:

```solidity
files[fileId] = FileData({id: fileId, ipfsHash: ipfsHash, owner: msg.sender});
```

The backend passes the `owner_address` from the upload form:

[`backend/app.py`](backend/app.py), lines 175–176:

```python
owner_address = request.form.get("owner_address") or os.environ.get("DEFAULT_OWNER_ADDRESS")
```

[`backend/app.py`](backend/app.py), lines 230–233:

```python
if ipfs_hash:
    try:
        blockchain_data = store_file(ipfs_hash, owner_address)
```

**No other identity storage exists.** No DB, no session, no IP logging.

---

### Question 11: Is there any login, signup, or wallet connect flow anywhere?

**Answer:** No.

- No login/signup backend routes
- No login/signup frontend UI
- No wallet connect logic
- Only a raw text input for `owner_address` in [`frontend/src/pages/Upload.jsx`](frontend/src/pages/Upload.jsx), lines 138–145:
  ```jsx
  <label className="mt-4 block">
    <span className="terminal-label text-[11px]">OWNER WALLET ADDRESS</span>
    <input
      value={ownerAddress}
      onChange={(event) => setOwnerAddress(event.target.value)}
      placeholder="0x..."
      className="mt-2 w-full border border-vault-border bg-black/30 px-4 py-3 font-display text-xs text-text-primary outline-none transition placeholder:text-text-muted focus:border-cyan focus:shadow-cyan"
    />
  </label>
  ```

---

## FILE OWNERSHIP

### Question 12: In the smart contract, show the exact struct or mapping that stores who owns which file.

**Answer:** File ownership is stored in the `FileData` struct and `File` struct.

In [`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), lines 7–11 and 15:

```solidity
struct FileData {
    uint256 id;
    string ipfsHash;
    address owner;
}

mapping(uint256 => FileData) public files;
```

In [`blockchain/FileStorage.sol`](blockchain/FileStorage.sol), lines 8–11 and 15:

```solidity
struct File {
    string ipfsHash;
    address owner;
}

mapping(uint => File) public files;
```

---

### Question 13: Is there a way to query "all files uploaded by address X"?

**Answer:** No.

Neither contract has a function that filters files by owner address. There is no reverse mapping like:

```solidity
mapping(address => uint[]) public filesByOwner;
```

---

### Question 14: If two people use the app, do their files get mixed together or separated? Trace through the code.

**Answer:** Mixed together.

1. **On-chain:** Files are stored by global `fileId` in a single mapping:
   [`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), lines 13–15:

   ```solidity
   uint256 public fileCount;
   mapping(uint256 => FileData) public files;
   ```

   There is no per-user namespace.

2. **On backend:** Encrypted files are stored in shared folders with no per-user segregation:
   [`backend/app.py`](backend/app.py), lines 32–38:

   ```python
   UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
   ENCRYPTED_FOLDER = os.path.join(BASE_DIR, "encrypted")
   DECRYPTED_FOLDER = os.path.join(BASE_DIR, "decrypted")

   os.makedirs(UPLOAD_FOLDER, exist_ok=True)
   os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
   os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
   ```

3. **On frontend:** Both users see the same mock file list:
   [`frontend/src/pages/Vault.jsx`](frontend/src/pages/Vault.jsx), lines 2–15:

   ```jsx
   import { mockFiles } from '../data/mockFiles.js';

   // ...
   const filtered = useMemo(() => {
     return mockFiles.filter((file) => { ... });
   }, [algorithm, query]);
   ```

---

## FRONTEND PROBLEMS

### Question 15: The current frontend has requesting access and granting access somewhere. Show exactly what the current frontend/index.html contains — paste the full file contents.

**Answer:** The frontend index.html is minimal:

[`frontend/index.html`](frontend/index.html), lines 1–12:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cold Vault Secure File Sharing</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**The actual UI is rendered by React components.** The relevant pages are:

- [`frontend/src/pages/Upload.jsx`](frontend/src/pages/Upload.jsx) — file upload only, no request/grant
- [`frontend/src/pages/Vault.jsx`](frontend/src/pages/Vault.jsx) — displays mock files, no request/grant
- [`frontend/src/pages/FileDetail.jsx`](frontend/src/pages/FileDetail.jsx) — shows file metadata, no request/grant

**The frontend has NO UI for requesting access or granting access.**

---

### Question 16: Why does having request and grant on the same page not make sense? Which of these two actions belongs to which role?

**Answer:** They are semantically opposed and require different actors.

From the contract code:

**requestAccess** is for a **non-owner** (someone who needs access):

[`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), lines 36–38:

```solidity
function requestAccess(uint256 fileId) public {
    require(fileId > 0 && fileId <= fileCount, "Invalid fileId");
    require(msg.sender != files[fileId].owner, "Owner has access");
```

**grantAccess** is for the **owner** (who decides to grant):

[`blockchain/FileAccess.sol`](blockchain/FileAccess.sol), lines 52–54:

```solidity
require(msg.sender == files[fileId].owner, "Only owner");
```

**Role mapping:**

- **REQUESTER (non-owner):** Can request access
- **OWNER:** Can grant or revoke access

**These are different people.** Having both on the same page would create a confusing UX where one person can only click "Request" and another can only click "Grant"—unless the page dynamically hides buttons based on who is logged in, which the app doesn't support.

---

## WHAT NEEDS TO BE BUILT

### Question 17: For a profile/account based system to work, list every backend change needed: new routes required, new contract functions required, new database or storage needed.

**Answer:** The codebase currently has **zero profile/account infrastructure**.

#### New Backend Routes Needed

1. `/auth/login` — Authenticate user (wallet or credentials)
2. `/auth/logout` — Invalidate session
3. `/auth/profile` — Get current user profile
4. `/user/<address>/files` — List files uploaded by user
5. `/user/<address>/pending-requests` — List pending access requests for user's files

#### New Contract Functions Needed

Both `FileAccess.sol` and `FileStorage.sol` are missing:

1. `getFilesByOwner(address owner)` — Query all files by owner
2. `getPendingAccessRequests(uint fileId)` — Get list of requesters (partially exists)
3. `revokeAccess(uint fileId, address user)` — Revoke access (missing in FileAccess)
4. Possible: emit events on state changes (already done, but incomplete)

#### New Database or Storage Needed

1. **User table:**
   - `user_id` (PK)
   - `wallet_address` (unique)
   - `profile_name`
   - `created_at`

2. **File ownership index table:**
   - `file_id` (FK to blockchain)
   - `owner_wallet_address` (FK to user)
   - `created_at`
   - (to avoid expensive blockchain queries)

3. **Access request history table:**
   - `request_id` (PK)
   - `file_id` (FK to blockchain)
   - `requester_address`
   - `status` (PENDING, GRANTED, DENIED)
   - `requested_at`
   - `resolved_at`

---

### Question 18: For role-based access to make sense, what are the correct roles? Define each role and what they can see and do in the app.

**Answer:** Based on the contract code and access patterns:

#### **ROLE: NONE (not defined, default for new users)**

- Can see: Public info only (if any)
- Can do:
  - Browse available files (if shared publicly)
  - Request access to files

#### **ROLE: VIEWER**

Defined in [`blockchain/FileStorage.sol`](blockchain/FileStorage.sol), line 6:

```solidity
enum Role { NONE, VIEWER, ADMIN }
```

- Can see: Only files where role >= VIEWER
- Can do:
  - Download/view granted files
  - See file metadata
  - Cannot modify or share further

#### **ROLE: ADMIN (equivalent to OWNER)**

- Can see: All files they own
- Can do:
  - Upload files
  - Grant VIEWER access to other users
  - Revoke access from users
  - Delete/manage their own files
  - See pending access requests

---

### Question 19: Based on everything above, list the minimum pages a corrected frontend needs. For each page, specify: who can see it, what data it reads from backend, what actions it performs.

**Answer:** The corrected app needs these pages:

#### **Page 1: Login / Connect Wallet**

- **Who:** Anyone (unauthenticated)
- **Data read:** None
- **Actions:**
  - Enter wallet address or login credentials
  - POST to `/auth/login` → get session token
  - Redirect to Dashboard

#### **Page 2: Dashboard / File Overview**

- **Who:** Authenticated users (VIEWER or ADMIN)
- **Data read:**
  - GET `/user/<address>/files` → user's uploaded files
  - GET `/user/<address>/pending-requests` → access requests waiting for owner approval
- **Actions:**
  - View all own files
  - See pending requests
  - Navigate to file detail or grant access page

#### **Page 3: Upload File**

- **Who:** Authenticated users (ADMIN intent)
- **Data read:** None
- **Actions:**
  - Select file, set sensitivity
  - POST to `/upload` with wallet address
  - On success: show file ID, IPFS hash, TX hash
  - Link to Dashboard or File Detail

#### **Page 4: File Detail / Manage Access**

- **Who:** Authenticated user (file owner only)
- **Data read:**
  - GET `/file/<file_id>` → metadata, owner, current permissions
  - GET `/file/<file_id>/access-list` → all users with access
  - GET `/file/<file_id>/pending-requests` → requesters waiting approval
- **Actions:**
  - View file metadata
  - Grant access to specific requesters (post to `/grant_access`)
  - Revoke access from users (post to `/revoke_access`)
  - Download own file

#### **Page 5: Browse Shared Files**

- **Who:** Authenticated users (VIEWER+ intent)
- **Data read:**
  - GET `/files/shared-with-me` → files user has access to
  - GET `/files/public` → publicly shared files (if any)
- **Actions:**
  - List files with access
  - Download/view file
  - (optional) Request access to non-shared files

#### **Page 6: Access Requests (For Requesters)**

- **Who:** Authenticated users requesting access
- **Data read:**
  - GET `/user/<address>/my-requests` → status of own requests
- **Actions:**
  - Request access to file (post to `/request_access`)
  - See request status
  - Cancel request (optional)

#### **Page 7: Profile / Account Settings**

- **Who:** Authenticated users
- **Data read:**
  - GET `/user/<address>/profile` → user info
- **Actions:**
  - View profile
  - Logout

---

## SUMMARY

### Single Biggest Architectural Flaw

**The frontend is disconnected from the backend's access-control implementation.**

The backend has:

- Contracts implementing owner-only grantAccess/revokeAccess
- Routes for `/request_access`, `/grant_access`, `/get_file`
- Access checks via `hasAccess()`

But the frontend:

- Shows **mock data** ([`frontend/src/data/mockFiles.js`](frontend/src/data/mockFiles.js))
- Downloads via `/decrypt/<filename>` **without any access checks**
- Has **no UI** for request/grant workflows
- Has **no concept of logged-in user or ownership**

**Result:** The access control is invisible to end users. Anyone can download any file by guessing the filename. The contract's security guarantees are completely bypassed.

---

### Key Findings Summary

| Aspect                      | Status     | Details                                      |
| --------------------------- | ---------- | -------------------------------------------- |
| **Roles defined?**          | ✅ Yes     | `NONE`, `VIEWER`, `ADMIN` in FileStorage.sol |
| **grantAccess owner-only?** | ✅ Yes     | Both contracts enforce `msg.sender == owner` |
| **Access request flow?**    | ✅ Yes     | Implemented in contract & backend            |
| **User profiles?**          | ❌ No      | No user table, sessions, or auth             |
| **Upload identity stored?** | ✅ Partial | Only on-chain in file struct                 |
| **Login flow?**             | ❌ No      | Only raw address input field                 |
| **File segregation?**       | ❌ No      | All files mixed in shared folders            |
| **Request/grant UI?**       | ❌ No      | Frontend has no access control UI            |
| **Revoke access?**          | ❌ No      | Backend route missing                        |
| **Backend wired?**          | ✅ Partial | Routes exist but not called from frontend    |

---

### Recommended Next Steps

1. **Implement user authentication** (wallet or credentials)
2. **Wire frontend to backend routes** for request/grant/revoke
3. **Replace mock data** with real API calls to `/user/<address>/files`
4. **Add role-based UI** (hide buttons based on user role/ownership)
5. **Implement revoke access** endpoint and contract function
6. **Add database** for user profiles and access request tracking
7. **Secure `/decrypt` endpoint** to check `hasAccess()` before returning file
