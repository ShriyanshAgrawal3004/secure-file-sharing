from flask import Flask, request, send_file
import os
import pickle
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "ml_model"))
if ML_MODEL_DIR not in sys.path:
    sys.path.append(ML_MODEL_DIR)
from blockchain_utils import (
    store_file,
    request_access,
    grant_access,
    has_access,
    get_file,
)
from predict import predict_algorithm

from crypto_utils import encrypt_aes, decrypt_aes, encrypt_chacha, decrypt_chacha
from ipfs_utils import upload_to_ipfs, IPFSUploadError
from web3 import Web3

from contract_config import CONTRACT_ADDRESS, ABI

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ENCRYPTED_FOLDER = os.path.join(BASE_DIR, "encrypted")
DECRYPTED_FOLDER = os.path.join(BASE_DIR, "decrypted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return "Encryption Server Running"


@app.route("/blockchain/health", methods=["GET"])
def blockchain_health():
    """Quick check to catch wrong Ganache RPC / wrong contract address / ABI mismatch."""

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

        # ABI sanity: make sure expected function names exist
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

        # Contract instantiation test
        contract = w3.eth.contract(address=checksum_addr, abi=ABI)
        # Light read-only call if code exists
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


# Helpful page when opening /upload in a browser
@app.route("/upload", methods=["GET"])
def upload_help():
        return """<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Upload file</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; }
            code { background: #f3f3f3; padding: 2px 6px; border-radius: 6px; }
            .card { max-width: 720px; padding: 16px 18px; border: 1px solid #e5e5e5; border-radius: 12px; }
            label { display: block; margin-top: 12px; }
            input[type=\"number\"], input[type=\"file\"] { margin-top: 6px; }
            button { margin-top: 16px; padding: 10px 14px; border-radius: 10px; border: 1px solid #ddd; background: #111; color: #fff; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class=\"card\">
            <h2>/upload (POST)</h2>
            <p>This endpoint only accepts <code>POST</code> multipart form data with fields:</p>
            <ul>
                <li><code>file</code>: the file to encrypt</li>
                <li><code>sensitivity</code>: integer</li>
                <li><code>owner_address</code>: wallet address (Ganache account)</li>
            </ul>

            <form action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\">
                <label>File
                    <input type=\"file\" name=\"file\" required />
                </label>
                <label>Sensitivity (integer)
                    <input type=\"number\" name=\"sensitivity\" value=\"5\" min=\"0\" step=\"1\" required />
                </label>
                <label>Owner address
                    <input type=\"text\" name=\"owner_address\" placeholder=\"0x...\" required style=\"width: 100%; max-width: 520px;\" />
                </label>
                <button type=\"submit\">Encrypt & Upload</button>
            </form>

            <p style=\"margin-top: 16px; color: #666\">Tip: if you’re calling from code, send multipart/form-data with the same field names.</p>
        </div>
    </body>
</html>"""


# 📤 Upload + Encrypt
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

    owner_address = request.form.get("owner_address")
    if not owner_address:
        return {"error": "Missing form field 'owner_address'"}, 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    algo = predict_algorithm(filepath, sensitivity)

    # Read file as binary
    with open(filepath, "rb") as f:
        data = f.read()

    # Encrypt
    # if algo == "AES":
    #     enc_data = encrypt_aes(data)
    # else:
    #     enc_data = encrypt_chacha(data)
    if algo == "AES":
        enc_data = encrypt_aes(data)
    elif algo == "CHACHA":
        enc_data = encrypt_chacha(data)
    else:
        enc_data = encrypt_aes(data)  # RSA hybrid later
    # Save encrypted data
    print(f"Predicted Algorithm: {algo}")
    enc_filename = file.filename + ".enc"
    enc_path = os.path.join(ENCRYPTED_FOLDER, enc_filename)

    with open(enc_path, "wb") as f:
        f.write(enc_data["ciphertext"])

    # Save keys separately (for now - later blockchain/IPFS)
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
    # Only store on-chain if we actually have an IPFS hash.
    # Also, never let blockchain issues crash the request.
    if ipfs_hash:
        try:
            blockchain_data = store_file(ipfs_hash, owner_address)
        except Exception as e:
            blockchain_error = {
                "message": "Blockchain store failed (is Ganache running and contract deployed?)",
                "details": str(e),
            }

    # resp = {
    #     "message": "File encrypted" if not ipfs_hash else "File encrypted and uploaded to IPFS",
    #     "file": enc_filename,
    #     "algorithm": algo,
    #     "ipfs_hash": ipfs_hash,
    # }
    # if ipfs_error:
    #     resp["ipfs_error"] = ipfs_error
    resp = {
        "message": "File encrypted"
        if not ipfs_hash
        else ("File encrypted and uploaded to IPFS" if not blockchain_data else "File encrypted, uploaded to IPFS, and stored on blockchain"),
        "file": enc_filename,
        "algorithm": algo,
        "ipfs_hash": ipfs_hash,
    }

    if blockchain_data:
        resp["file_id"] = blockchain_data.get("file_id")
        resp["transaction_hash"] = blockchain_data.get("tx_hash")

    if ipfs_error:
        resp["ipfs_error"] = ipfs_error

    if blockchain_error:
        resp["blockchain_error"] = blockchain_error

    return resp
  

# 📥 Decrypt + Download
@app.route("/decrypt/<filename>", methods=["GET"])
def decrypt_file(filename):
    enc_path = os.path.join(ENCRYPTED_FOLDER, filename)

    with open(enc_path, "rb") as f:
        ciphertext = f.read()

    with open(enc_path + ".meta", "rb") as f:
        enc_data = pickle.load(f)

    enc_data["ciphertext"] = ciphertext

    # Detect algorithm
    if "tag" in enc_data:
        decrypted = decrypt_aes(enc_data)
    else:
        decrypted = decrypt_chacha(enc_data)

    output_path = os.path.join(DECRYPTED_FOLDER, "dec_" + filename.replace(".enc", ""))

    with open(output_path, "wb") as f:
        f.write(decrypted)

    return send_file(output_path, as_attachment=True)

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