from flask import Flask, request, send_file
import os
import pickle
import sys
sys.path.append("../ml_model")
from blockchain_utils import store_file
from predict import predict_algorithm

from crypto_utils import encrypt_aes, decrypt_aes, encrypt_chacha, decrypt_chacha
from ipfs_utils import upload_to_ipfs, IPFSUploadError

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ENCRYPTED_FOLDER = os.path.join(BASE_DIR, "encrypted")
DECRYPTED_FOLDER = os.path.join(BASE_DIR, "decrypted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return "Encryption Server Running"


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
            </ul>

            <form action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\">
                <label>File
                    <input type=\"file\" name=\"file\" required />
                </label>
                <label>Sensitivity (integer)
                    <input type=\"number\" name=\"sensitivity\" value=\"5\" min=\"0\" step=\"1\" required />
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

    # resp = {
    #     "message": "File encrypted" if not ipfs_hash else "File encrypted and uploaded to IPFS",
    #     "file": enc_filename,
    #     "algorithm": algo,
    #     "ipfs_hash": ipfs_hash,
    # }
    # if ipfs_error:
    #     resp["ipfs_error"] = ipfs_error
    tx_hash = store_file(ipfs_hash)
    return {
    "message": "File stored on blockchain",
    "ipfs_hash": ipfs_hash,
    "transaction_hash": tx_hash,
    "algorithm": algo
     }
  

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, port=port)