from datetime import datetime
import uuid
import os
import pickle
import sys
import base64

from dotenv import load_dotenv
from flask import Flask, request, send_file, session
from flask_cors import CORS
from web3 import Web3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ML_MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "ml_model"))
if ML_MODEL_DIR not in sys.path:
    sys.path.append(ML_MODEL_DIR)

from blockchain_utils import (  # noqa: E402
    get_file,
    grant_access,
    has_access,
    request_access,
    store_file,
)
from contract_config import ABI, CONTRACT_ADDRESS  # noqa: E402
from crypto_utils import (  # noqa: E402
    decrypt_aes,
    decrypt_chacha,
    decrypt_rsa,
    encrypt_aes,
    encrypt_chacha,
    encrypt_rsa,
    generate_rsa_keypair,
)
from database import AccessRequest, FileIndex, User, get_db, init_db  # noqa: E402
from ipfs_utils import IPFSUploadError, upload_to_ipfs  # noqa: E402
from predict import predict_algorithm  # noqa: E402
from pre_proxy import (  # noqa: E402
    ensure_wallet_keypair,
    load_public_key_pem,
    unwrap_key_for_wallet_b64,
    wrap_key_for_wallet_b64,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-cold-vault-secret")
CORS(
    app,
    resources={r"/*": {"origins": ["http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://localhost:5173", "http://localhost:5174"]}},
    supports_credentials=True,
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ENCRYPTED_FOLDER = os.path.join(BASE_DIR, "encrypted")
DECRYPTED_FOLDER = os.path.join(BASE_DIR, "decrypted")
KEYS_FOLDER = os.path.join(BASE_DIR, "keys")
PRE_FOLDER = os.path.join(BASE_DIR, "pre")
PRE_SHARES_FOLDER = os.path.join(PRE_FOLDER, "shares")
PRE_META_FOLDER = os.path.join(PRE_FOLDER, "meta")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
os.makedirs(KEYS_FOLDER, exist_ok=True)
os.makedirs(PRE_FOLDER, exist_ok=True)
os.makedirs(PRE_SHARES_FOLDER, exist_ok=True)
os.makedirs(PRE_META_FOLDER, exist_ok=True)
init_db()


def normalize_wallet(wallet):
    return (wallet or "").strip()


def is_valid_address(addr):
    """Check if address is valid Ethereum address format"""
    if not addr or len(addr) != 42:
        return False
    if not addr.startswith("0x"):
        return False
    try:
        int(addr[2:], 16)
        return True
    except ValueError:
        return False


def _pre_enc_path(file_id: int) -> str:
    return os.path.join(PRE_FOLDER, f"{int(file_id)}.pre.enc")


def _pre_meta_path(file_id: int) -> str:
    return os.path.join(PRE_META_FOLDER, f"{int(file_id)}.meta.pkl")


def _pre_share_key_path(file_id: int, receiver_wallet: str) -> str:
    safe = normalize_wallet(receiver_wallet).lower()
    return os.path.join(PRE_SHARES_FOLDER, f"{int(file_id)}__{safe}.key.b64")


def _aes_gcm_encrypt_bytes(plaintext: bytes):
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return key, cipher.nonce, tag, ciphertext


def _aes_gcm_decrypt_bytes(key: bytes, nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


@app.route("/pre/public-key/<wallet>", methods=["GET"])
def pre_public_key(wallet):
    wallet = normalize_wallet(wallet)
    if not is_valid_address(wallet):
        return {"error": "Invalid wallet address"}, 400
    ensure_wallet_keypair(KEYS_FOLDER, wallet)
    return {"wallet_address": wallet, "public_key_pem": load_public_key_pem(KEYS_FOLDER, wallet)}


@app.route("/pre/upload", methods=["POST"])
def pre_upload_file():
    """Proxy re-encryption (simulation) upload.

    Flow:
      - File bytes encrypted with AES-GCM using random Key A
      - Key A is wrapped with the owner's RSA public key (stored on server per wallet)
      - Later, owner can generate a re-encryption key (A->B) for a receiver
      - Proxy stores the receiver-wrapped key so receiver can decrypt using Key B
    """
    if "file" not in request.files:
        return {"error": "Missing file field 'file'"}, 400

    file = request.files["file"]
    if not file or not file.filename:
        return {"error": "No file selected"}, 400

    sensitivity_raw = request.form.get("sensitivity")
    if sensitivity_raw is None:
        return {"error": "Missing form field 'sensitivity'"}, 400
    try:
        sensitivity = int(sensitivity_raw)
    except ValueError:
        return {"error": "Invalid 'sensitivity' (must be integer)"}, 400

    owner_address = normalize_wallet(request.form.get("owner_address") or os.environ.get("DEFAULT_OWNER_ADDRESS"))
    if not is_valid_address(owner_address):
        return {"error": "Missing or invalid owner wallet address"}, 400

    # Read bytes once (no plaintext exposure beyond server memory)
    plaintext = file.read()
    file_size = len(plaintext)

    key_a, nonce, tag, ciphertext = _aes_gcm_encrypt_bytes(plaintext)
    # Ensure owner has RSA keys and wrap Key A
    ensure_wallet_keypair(KEYS_FOLDER, owner_address)
    wrapped_key_owner_b64 = wrap_key_for_wallet_b64(KEYS_FOLDER, owner_address, key_a)

    # Write encrypted payload to a temp path until we have a chain file_id
    tmp_name = f"tmp_{uuid.uuid4().hex}.pre.enc"
    tmp_enc_path = os.path.join(PRE_FOLDER, tmp_name)
    with open(tmp_enc_path, "wb") as f:
        f.write(ciphertext)

    # Upload encrypted blob to IPFS (optional), then store hash on-chain
    ipfs_hash = None
    ipfs_error = None
    try:
        ipfs_hash = upload_to_ipfs(tmp_enc_path)
    except IPFSUploadError as e:
        ipfs_error = {
            "message": str(e),
            "status_code": getattr(e, "status_code", None),
            "details": getattr(e, "details", None),
        }

    blockchain_data = None
    blockchain_error = None
    if ipfs_hash:
        try:
            blockchain_data = store_file(ipfs_hash, owner_address)
        except Exception as e:
            blockchain_error = {
                "message": "Blockchain store failed (is Ganache running and contract deployed?)",
                "details": str(e),
            }

    resp = {
        "message": "PRE file encrypted"
        if not ipfs_hash
        else (
            "PRE file encrypted and uploaded to IPFS"
            if not blockchain_data
            else "PRE file encrypted, uploaded to IPFS, and stored on blockchain"
        ),
        "original_filename": file.filename,
        "algorithm": "AES_PRE",
        "ipfs_hash": ipfs_hash,
    }

    if blockchain_data:
        file_id = int(blockchain_data.get("file_id"))
        tx_hash = blockchain_data.get("tx_hash")

        # Move temp ciphertext into stable file_id path
        enc_path = _pre_enc_path(file_id)
        os.replace(tmp_enc_path, enc_path)

        meta = {
            "version": 1,
            "algorithm": "AES_PRE",
            "owner_wallet": owner_address,
            "original_filename": file.filename,
            "file_size": file_size,
            "sensitivity": sensitivity,
            "ipfs_hash": ipfs_hash,
            "tx_hash": tx_hash,
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "tag_b64": base64.b64encode(tag).decode("ascii"),
            # Key A wrapped to owner; used only to generate re-encryption keys
            "wrapped_key_owner_b64": wrapped_key_owner_b64,
        }
        with open(_pre_meta_path(file_id), "wb") as f:
            pickle.dump(meta, f)

        # Mirror into DB so existing UI can list it
        db = get_db()
        get_or_create_user(db, owner_address)
        file_row = db.query(FileIndex).filter(FileIndex.file_id == file_id).first()
        if not file_row:
            file_row = FileIndex(file_id=file_id)
            db.add(file_row)
        file_row.owner_wallet = owner_address
        file_row.original_filename = file.filename
        file_row.file_size = file_size
        file_row.algorithm = "AES_PRE"
        file_row.ipfs_hash = ipfs_hash
        file_row.tx_hash = tx_hash
        file_row.sensitivity = sensitivity
        db.commit()

        resp["file_id"] = file_id
        resp["transaction_hash"] = tx_hash
    else:
        # keep temp file for debugging if chain storage didn't happen
        resp["tmp_enc_path"] = tmp_enc_path

    if ipfs_error:
        resp["ipfs_error"] = ipfs_error
    if blockchain_error:
        resp["blockchain_error"] = blockchain_error

    return resp


@app.route("/pre/generate_rekey", methods=["POST"])
def pre_generate_rekey():
    """Generate a re-encryption key (A->B) as an RSA-OAEP wrapped AES key for receiver.

    This is a simplified simulation: re-encryption key is `Enc(pk_receiver, KeyA)`.
    """
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    owner_address = normalize_wallet(data.get("owner_address"))
    receiver_address = normalize_wallet(data.get("receiver_address"))

    if file_id is None or not is_valid_address(owner_address) or not is_valid_address(receiver_address):
        return {"error": "Required JSON fields: file_id, valid owner_address, valid receiver_address"}, 400

    meta_path = _pre_meta_path(int(file_id))
    if not os.path.exists(meta_path):
        return {"error": "PRE metadata not found (was the file uploaded via /pre/upload?)"}, 404

    with open(meta_path, "rb") as f:
        meta = pickle.load(f)

    if normalize_wallet(meta.get("owner_wallet")).lower() != owner_address.lower():
        return {"error": "Only the owner can generate re-encryption keys for this file"}, 403

    wrapped_owner_b64 = meta.get("wrapped_key_owner_b64")
    if not wrapped_owner_b64:
        return {"error": "Missing wrapped owner key in metadata"}, 500

    # Unwrap KeyA using owner's private key, then wrap for receiver.
    key_a = unwrap_key_for_wallet_b64(KEYS_FOLDER, owner_address, wrapped_owner_b64)
    ensure_wallet_keypair(KEYS_FOLDER, receiver_address)
    rekey_b64 = wrap_key_for_wallet_b64(KEYS_FOLDER, receiver_address, key_a)

    return {
        "file_id": int(file_id),
        "owner_address": owner_address,
        "receiver_address": receiver_address,
        "re_encryption_key_b64": rekey_b64,
    }


@app.route("/pre/transform", methods=["POST"])
def pre_transform():
    """Proxy stores the receiver-wrapped AES key as the 'transformed ciphertext package'."""
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    receiver_address = normalize_wallet(data.get("receiver_address"))
    rekey_b64 = data.get("re_encryption_key_b64")

    if file_id is None or not is_valid_address(receiver_address) or not rekey_b64:
        return {"error": "Required JSON fields: file_id, valid receiver_address, re_encryption_key_b64"}, 400

    meta_path = _pre_meta_path(int(file_id))
    enc_path = _pre_enc_path(int(file_id))
    if not os.path.exists(meta_path) or not os.path.exists(enc_path):
        return {"error": "PRE file not found"}, 404

    # Store the transformed key blob. Proxy never needs plaintext.
    out_path = _pre_share_key_path(int(file_id), receiver_address)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(rekey_b64).strip())

    return {"message": "Transformed package stored", "file_id": int(file_id), "receiver_address": receiver_address}


@app.route("/pre/download/<int:file_id>", methods=["GET"])
def pre_download(file_id: int):
    """Receiver downloads and decrypts using their private key + wrapped KeyA."""
    wallet_address = normalize_wallet(request.args.get("wallet_address"))
    if not is_valid_address(wallet_address):
        return {"error": "Missing or invalid query param: wallet_address"}, 400

    # Enforce blockchain access
    try:
        allowed = has_access(int(file_id), wallet_address)
    except Exception as e:
        return {"error": str(e)}, 400
    if not allowed:
        return {"error": "Access denied"}, 403

    enc_path = _pre_enc_path(int(file_id))
    meta_path = _pre_meta_path(int(file_id))
    if not os.path.exists(enc_path) or not os.path.exists(meta_path):
        return {"error": "PRE encrypted file missing"}, 404

    share_key_path = _pre_share_key_path(int(file_id), wallet_address)
    if not os.path.exists(share_key_path):
        return {"error": "No PRE transformed key found for this receiver"}, 404

    with open(meta_path, "rb") as f:
        meta = pickle.load(f)
    with open(enc_path, "rb") as f:
        ciphertext = f.read()
    with open(share_key_path, "r", encoding="utf-8") as f:
        wrapped_key_receiver_b64 = f.read().strip()

    nonce = base64.b64decode(meta.get("nonce_b64", ""))
    tag = base64.b64decode(meta.get("tag_b64", ""))
    key_a = unwrap_key_for_wallet_b64(KEYS_FOLDER, wallet_address, wrapped_key_receiver_b64)

    plaintext = _aes_gcm_decrypt_bytes(key_a, nonce, tag, ciphertext)

    # Write to decrypted folder and send
    original_filename = meta.get("original_filename") or f"file_{file_id}"
    out_path = os.path.join(DECRYPTED_FOLDER, f"pre_dec_{file_id}__{original_filename}")
    with open(out_path, "wb") as f:
        f.write(plaintext)
    return send_file(out_path, as_attachment=True, download_name=original_filename)


def user_payload(user):
    return {
        "wallet_address": user.wallet_address,
        "display_name": user.display_name,
        "created_at": user.created_at.isoformat(),
    }


def file_payload(file_row):
    return {
        "file_id": file_row.file_id,
        "owner_wallet": file_row.owner_wallet,
        "original_filename": file_row.original_filename,
        "file_size": file_row.file_size,
        "algorithm": file_row.algorithm,
        "ipfs_hash": file_row.ipfs_hash,
        "tx_hash": file_row.tx_hash,
        "sensitivity": file_row.sensitivity,
        "created_at": file_row.created_at.isoformat(),
    }


def request_payload(access_row, file_row=None):
    payload = {
        "id": access_row.id,
        "file_id": access_row.file_id,
        "requester_address": access_row.requester_address,
        "status": access_row.status,
        "requested_at": access_row.requested_at.isoformat(),
        "resolved_at": access_row.resolved_at.isoformat() if access_row.resolved_at else None,
    }
    if file_row:
        payload.update(
            {
                "filename": file_row.original_filename,
                "owner_wallet": file_row.owner_wallet,
                "algorithm": file_row.algorithm,
                "file_size": file_row.file_size,
                "ipfs_hash": file_row.ipfs_hash,
                "tx_hash": file_row.tx_hash,
                "sensitivity": file_row.sensitivity,
                "created_at": file_row.created_at.isoformat(),
            }
        )
    return payload


def get_or_create_user(db, wallet):
    wallet = normalize_wallet(wallet)
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if user:
        return user
    user = User(wallet_address=wallet)
    db.add(user)
    db.flush()
    return user


@app.teardown_appcontext
def remove_db_session(_exception=None):
    from database import SessionLocal

    SessionLocal.remove()


@app.route("/")
def home():
    return "Encryption Server Running"


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    wallet = normalize_wallet(data.get("wallet_address"))
    if not is_valid_address(wallet):
        return {"error": "Invalid wallet address"}, 400

    db = get_db()
    user = get_or_create_user(db, wallet)
    db.commit()
    session["wallet_address"] = user.wallet_address
    return user_payload(user)


@app.route("/auth/me", methods=["GET"])
def me():
    wallet = session.get("wallet_address")
    if not wallet:
        return {"error": "Not authenticated"}, 401

    db = get_db()
    user = db.query(User).filter(User.wallet_address == wallet).first()
    if not user:
        session.clear()
        return {"error": "Not authenticated"}, 401
    return user_payload(user)


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return {"message": "Logged out"}


@app.route("/user/<wallet>/profile", methods=["PUT"])
def update_profile(wallet):
    data = request.get_json(silent=True) or {}
    db = get_db()
    user = db.query(User).filter(User.wallet_address == normalize_wallet(wallet)).first()
    if not user:
        return {"error": "User not found"}, 404
    user.display_name = data.get("display_name") or None
    db.commit()
    return user_payload(user)


@app.route("/user/<wallet>/files", methods=["GET"])
def user_files(wallet):
    db = get_db()
    files = (
        db.query(FileIndex)
        .filter(FileIndex.owner_wallet == normalize_wallet(wallet))
        .order_by(FileIndex.created_at.desc())
        .all()
    )
    return {"files": [file_payload(row) for row in files]}


@app.route("/user/<wallet>/pending-requests", methods=["GET"])
def pending_requests(wallet):
    db = get_db()
    rows = (
        db.query(AccessRequest, FileIndex)
        .join(FileIndex, AccessRequest.file_id == FileIndex.file_id)
        .filter(FileIndex.owner_wallet == normalize_wallet(wallet), AccessRequest.status == "PENDING")
        .order_by(AccessRequest.requested_at.desc())
        .all()
    )
    return {"requests": [request_payload(access, file_row) for access, file_row in rows]}


@app.route("/user/<wallet>/my-requests", methods=["GET"])
def my_requests(wallet):
    db = get_db()
    rows = (
        db.query(AccessRequest, FileIndex)
        .join(FileIndex, AccessRequest.file_id == FileIndex.file_id)
        .filter(AccessRequest.requester_address == normalize_wallet(wallet))
        .order_by(AccessRequest.requested_at.desc())
        .all()
    )
    return {"requests": [request_payload(access, file_row) for access, file_row in rows]}


@app.route("/file/<int:file_id>", methods=["GET"])
def file_detail(file_id):
    db = get_db()
    file_row = db.query(FileIndex).filter(FileIndex.file_id == int(file_id)).first()
    if not file_row:
        return {"error": "File not found"}, 404
    return file_payload(file_row)


@app.route("/file/<int:file_id>/access-list", methods=["GET"])
def file_access_list(file_id):
    status = (request.args.get("status") or "GRANTED").upper()
    if status not in {"PENDING", "GRANTED", "DENIED", "ALL"}:
        return {"error": "Invalid status"}, 400

    db = get_db()
    query = db.query(AccessRequest).filter(AccessRequest.file_id == int(file_id))
    if status != "ALL":
        query = query.filter(AccessRequest.status == status)
    rows = query.order_by(AccessRequest.requested_at.desc()).all()
    return {"requests": [request_payload(row) for row in rows]}


@app.route("/blockchain/health", methods=["GET"])
def blockchain_health():
    rpc_url = os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        connected = bool(w3.is_connected())
        info = {
            "connected": connected,
            "rpc_url": rpc_url,
            "contract_address": CONTRACT_ADDRESS,
        }
        if not connected:
            return info, 503

        try:
            info["chain_id"] = int(w3.eth.chain_id)
        except Exception as e:
            info["chain_id_error"] = str(e)

        checksum_addr = w3.to_checksum_address(CONTRACT_ADDRESS)
        code = w3.eth.get_code(checksum_addr)
        info["has_code"] = bool(code and code != b"\x00")
        info["code_size"] = len(code or b"")
        abi_fn_names = sorted(
            {
                entry.get("name")
                for entry in ABI
                if isinstance(entry, dict) and entry.get("type") == "function"
            }
            - {None}
        )
        info["abi_functions"] = abi_fn_names
        expected = {"storeFile", "requestAccess", "grantAccess", "hasAccess", "getFile"}
        info["abi_has_expected"] = expected.issubset(set(abi_fn_names))

        contract = w3.eth.contract(address=checksum_addr, abi=ABI)
        if info["has_code"]:
            try:
                info["fileCount"] = int(contract.functions.fileCount().call())
            except Exception as e:
                info["fileCount_error"] = str(e)

        status = 200 if info["has_code"] else 503
        return info, status
    except Exception as e:
        return {
            "connected": False,
            "rpc_url": rpc_url,
            "contract_address": CONTRACT_ADDRESS,
            "error": str(e),
        }, 503


@app.route("/upload", methods=["GET"])
def upload_help():
    return "POST multipart form data with file, sensitivity, owner_address"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "Missing file field 'file'"}, 400

    file = request.files["file"]
    if not file or not file.filename:
        return {"error": "No file selected"}, 400

    sensitivity_raw = request.form.get("sensitivity")
    if sensitivity_raw is None:
        return {"error": "Missing form field 'sensitivity'"}, 400

    try:
        sensitivity = int(sensitivity_raw)
    except ValueError:
        return {"error": "Invalid 'sensitivity' (must be integer)"}, 400

    owner_address = normalize_wallet(request.form.get("owner_address") or os.environ.get("DEFAULT_OWNER_ADDRESS"))
    if not is_valid_address(owner_address):
        return {"error": "Missing or invalid owner wallet address"}, 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    algo_raw = predict_algorithm(filepath, sensitivity)
    algo = str(algo_raw).upper() if algo_raw is not None else ""

    with open(filepath, "rb") as f:
        data = f.read()

    if algo == "AES":
        enc_data = encrypt_aes(data)
        key_id = None
    elif algo in {"CHACHA", "CHACHA20", "CHACHA-20"}:
        algo = "CHACHA"
        enc_data = encrypt_chacha(data)
        key_id = None
    elif algo == "RSA":
        private_pem, public_pem = generate_rsa_keypair()
        enc_data = encrypt_rsa(data, public_pem)
        key_id = str(uuid.uuid4())
        with open(os.path.join(KEYS_FOLDER, f"{key_id}_private.pem"), "w") as kf:
            kf.write(private_pem)
        with open(os.path.join(KEYS_FOLDER, f"{key_id}_public.pem"), "w") as kf:
            kf.write(public_pem)
    else:
        algo = "AES"
        enc_data = encrypt_aes(data)
        key_id = None

    if isinstance(enc_data, bytes):
        ciphertext = enc_data
        meta_payload = {"rsa": True, "key_id": key_id}
    else:
        ciphertext = enc_data["ciphertext"]
        meta_payload = enc_data

    enc_filename = file.filename + ".enc"
    enc_path = os.path.join(ENCRYPTED_FOLDER, enc_filename)
    with open(enc_path, "wb") as f:
        f.write(ciphertext)
    with open(enc_path + ".meta", "wb") as f:
        pickle.dump(meta_payload, f)

    ipfs_hash = None
    ipfs_error = None
    try:
        ipfs_hash = upload_to_ipfs(enc_path)
    except IPFSUploadError as e:
        ipfs_error = {
            "message": str(e),
            "status_code": getattr(e, "status_code", None),
            "details": getattr(e, "details", None),
        }

    blockchain_data = None
    blockchain_error = None
    if ipfs_hash:
        try:
            blockchain_data = store_file(ipfs_hash, owner_address)
        except Exception as e:
            blockchain_error = {
                "message": "Blockchain store failed (is Ganache running and contract deployed?)",
                "details": str(e),
            }

    resp = {
        "message": "File encrypted"
        if not ipfs_hash
        else (
            "File encrypted and uploaded to IPFS"
            if not blockchain_data
            else "File encrypted, uploaded to IPFS, and stored on blockchain"
        ),
        "file": enc_filename,
        "original_filename": file.filename,
        "algorithm": algo,
        "ipfs_hash": ipfs_hash,
        "key_id": key_id,
    }

    if blockchain_data:
        file_id = int(blockchain_data.get("file_id"))
        tx_hash = blockchain_data.get("tx_hash")
        db = get_db()
        get_or_create_user(db, owner_address)
        file_row = db.query(FileIndex).filter(FileIndex.file_id == file_id).first()
        if not file_row:
            file_row = FileIndex(file_id=file_id)
            db.add(file_row)
        file_row.owner_wallet = owner_address
        file_row.original_filename = file.filename
        file_row.file_size = file_size
        file_row.algorithm = algo
        file_row.ipfs_hash = ipfs_hash
        file_row.tx_hash = tx_hash
        file_row.sensitivity = sensitivity
        db.commit()
        resp["file_id"] = file_id
        resp["transaction_hash"] = tx_hash

    if ipfs_error:
        resp["ipfs_error"] = ipfs_error
    if blockchain_error:
        resp["blockchain_error"] = blockchain_error

    return resp


@app.route("/decrypt/<filename>", methods=["GET"])
def decrypt_file(filename):
    wallet_address = normalize_wallet(request.args.get("wallet_address"))
    if not is_valid_address(wallet_address):
        return {"error": "Missing or invalid query param: wallet_address"}, 400

    original_filename = filename[:-4] if filename.endswith(".enc") else filename
    db = get_db()
    file_row = db.query(FileIndex).filter(FileIndex.original_filename == original_filename).first()
    if not file_row:
        return {"error": "File not found"}, 404

    try:
        allowed = has_access(file_row.file_id, wallet_address)
    except Exception as e:
        return {"error": str(e)}, 400

    if not allowed:
        return {"error": "Access denied"}, 403

    enc_filename = original_filename + ".enc"
    enc_path = os.path.join(ENCRYPTED_FOLDER, enc_filename)
    if not os.path.exists(enc_path):
        return {"error": "Encrypted file missing from server"}, 404

    with open(enc_path, "rb") as f:
        ciphertext = f.read()
    with open(enc_path + ".meta", "rb") as f:
        enc_data = pickle.load(f)

    key_id = request.args.get("key_id")
    if not key_id and isinstance(enc_data, dict):
        key_id = enc_data.get("key_id")

    if key_id:
        private_key_path = os.path.join(KEYS_FOLDER, f"{key_id}_private.pem")
        if not os.path.exists(private_key_path):
            return {"error": "RSA key not found"}, 404
        with open(private_key_path, "r") as kf:
            private_pem = kf.read()
        decrypted = decrypt_rsa(ciphertext, private_pem)
    else:
        enc_data["ciphertext"] = ciphertext
        decrypted = decrypt_aes(enc_data) if "tag" in enc_data else decrypt_chacha(enc_data)

    output_path = os.path.join(DECRYPTED_FOLDER, "dec_" + original_filename)
    with open(output_path, "wb") as f:
        f.write(decrypted)

    return send_file(output_path, as_attachment=True, download_name=original_filename)


@app.route("/request_access", methods=["POST"])
def request_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    user_address = normalize_wallet(data.get("user_address"))

    if file_id is None or not is_valid_address(user_address):
        return {"error": "Required JSON fields: file_id, valid user_address"}, 400

    db = get_db()
    file_row = db.query(FileIndex).filter(FileIndex.file_id == int(file_id)).first()
    if not file_row:
        return {"error": "File not found"}, 404
    if file_row.owner_wallet.lower() == user_address.lower():
        return {"error": "Owner already has access"}, 400

    try:
        tx_hash = request_access(int(file_id), user_address)
    except Exception as e:
        return {"error": str(e)}, 403

    get_or_create_user(db, user_address)
    access_row = (
        db.query(AccessRequest)
        .filter(AccessRequest.file_id == int(file_id), AccessRequest.requester_address == user_address)
        .first()
    )
    if access_row:
        access_row.status = "PENDING"
        access_row.resolved_at = None
    else:
        access_row = AccessRequest(file_id=int(file_id), requester_address=user_address, status="PENDING")
        db.add(access_row)
    db.commit()
    return {"message": "Access requested", "transaction_hash": tx_hash, "request": request_payload(access_row, file_row)}


@app.route("/grant_access", methods=["POST"])
def grant_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    owner_address = normalize_wallet(data.get("owner_address"))
    user_address = normalize_wallet(data.get("user_address"))

    if file_id is None or not is_valid_address(owner_address) or not is_valid_address(user_address):
        return {"error": "Required JSON fields: file_id, valid owner_address, valid user_address"}, 400

    db = get_db()
    file_row = db.query(FileIndex).filter(FileIndex.file_id == int(file_id)).first()
    if not file_row:
        return {"error": "File not found"}, 404
    if normalize_wallet(file_row.owner_wallet).lower() != owner_address.lower():
        return {"error": "Only the stored file owner can grant access"}, 403

    try:
        tx_hash = grant_access(int(file_id), owner_address, user_address)
    except Exception as e:
        return {"error": str(e)}, 403

    access_row = (
        db.query(AccessRequest)
        .filter(AccessRequest.file_id == int(file_id), AccessRequest.requester_address == user_address)
        .first()
    )
    if not access_row:
        access_row = AccessRequest(file_id=int(file_id), requester_address=user_address)
        db.add(access_row)
    access_row.status = "GRANTED"
    access_row.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Access granted", "transaction_hash": tx_hash}


@app.route("/deny_access", methods=["POST"])
def deny_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    owner_address = normalize_wallet(data.get("owner_address"))
    user_address = normalize_wallet(data.get("user_address"))

    if file_id is None or not is_valid_address(owner_address) or not is_valid_address(user_address):
        return {"error": "Required JSON fields: file_id, valid owner_address, valid user_address"}, 400

    db = get_db()
    file_row = db.query(FileIndex).filter(FileIndex.file_id == int(file_id)).first()
    if not file_row:
        return {"error": "File not found"}, 404
    if normalize_wallet(file_row.owner_wallet).lower() != owner_address.lower():
        return {"error": "Only the stored file owner can deny access"}, 403

    access_row = (
        db.query(AccessRequest)
        .filter(AccessRequest.file_id == int(file_id), AccessRequest.requester_address == user_address)
        .first()
    )
    if not access_row:
        return {"error": "Access request not found"}, 404

    if access_row.status == "DENIED":
        return {"message": "Access already denied"}

    if access_row.status == "GRANTED":
        return {"error": "Granted access must be revoked from the blockchain-aware flow"}, 400

    access_row.status = "DENIED"
    access_row.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Access denied"}


@app.route("/get_file/<int:file_id>", methods=["GET"])
def get_file_api(file_id):
    user_address = request.args.get("user_address")
    if not user_address:
        return {"error": "Missing query param: user_address"}, 400

    try:
        allowed = has_access(int(file_id), user_address)
    except Exception as e:
        return {"error": str(e)}, 400

    if not allowed:
        return {"error": "Access denied"}, 403

    try:
        ipfs_hash = get_file(int(file_id), user_address)
        return {"ipfs_hash": ipfs_hash}
    except Exception as e:
        return {"error": str(e)}, 403


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, port=port)
