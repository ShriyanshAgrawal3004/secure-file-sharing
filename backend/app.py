from datetime import datetime
import os
import pickle
import sys

from dotenv import load_dotenv
from flask import Flask, request, send_file, session
from flask_cors import CORS
from web3 import Web3

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
    revoke_access,
    store_file,
)
from contract_config import ABI, CONTRACT_ADDRESS  # noqa: E402
from crypto_utils import decrypt_aes, decrypt_chacha, encrypt_aes, encrypt_chacha  # noqa: E402
from database import AccessRequest, FileIndex, User, get_db, init_db  # noqa: E402
from ipfs_utils import IPFSUploadError, upload_to_ipfs  # noqa: E402
from predict import predict_algorithm  # noqa: E402

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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
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
    elif algo in {"CHACHA", "CHACHA20", "CHACHA-20"}:
        algo = "CHACHA"
        enc_data = encrypt_chacha(data)
    else:
        algo = "AES"
        enc_data = encrypt_aes(data)

    enc_filename = file.filename + ".enc"
    enc_path = os.path.join(ENCRYPTED_FOLDER, enc_filename)
    with open(enc_path, "wb") as f:
        f.write(enc_data["ciphertext"])
    with open(enc_path + ".meta", "wb") as f:
        pickle.dump(enc_data, f)

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

    try:
        tx_hash = grant_access(int(file_id), owner_address, user_address)
    except Exception as e:
        return {"error": str(e)}, 403

    db = get_db()
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


@app.route("/revoke_access", methods=["POST"])
def revoke_access_api():
    data = request.get_json(silent=True) or {}
    file_id = data.get("file_id")
    owner_address = normalize_wallet(data.get("owner_address"))
    user_address = normalize_wallet(data.get("user_address"))

    if file_id is None or not is_valid_address(owner_address) or not is_valid_address(user_address):
        return {"error": "Required JSON fields: file_id, valid owner_address, valid user_address"}, 400

    try:
        tx_hash = revoke_access(int(file_id), owner_address, user_address)
    except Exception as e:
        return {"error": str(e)}, 403

    db = get_db()
    access_row = (
        db.query(AccessRequest)
        .filter(AccessRequest.file_id == int(file_id), AccessRequest.requester_address == user_address)
        .first()
    )
    if access_row:
        access_row.status = "DENIED"
        access_row.resolved_at = datetime.utcnow()
        db.commit()
    return {"message": "Access revoked", "transaction_hash": tx_hash}


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
