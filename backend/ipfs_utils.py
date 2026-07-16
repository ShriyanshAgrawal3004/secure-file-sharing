import requests
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Pinata credentials are expected in `backend/.env`:
#   PINATA_API_KEY=...
#   PINATA_SECRET_API_KEY=...
#
# If you see errors like NO_SCOPES_FOUND, your API key doesn't have the required
# Pinata scopes/permissions for pinning. Either create a new key with pinning
# access or adjust scopes in Pinata's dashboard.

PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET = os.getenv("PINATA_SECRET_API_KEY")

PINATA_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"


class IPFSUploadError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


def upload_to_ipfs(filepath):
    """Upload a file to IPFS using Pinata.

    Returns:
        str: IpfsHash on success

    Raises:
        IPFSUploadError: when upload fails (auth, scopes, network, etc.)
    """
    if not PINATA_API_KEY or not PINATA_SECRET:
        raise IPFSUploadError(
            "Missing Pinata credentials. Set PINATA_API_KEY and PINATA_SECRET_API_KEY in backend/.env",
            status_code=None,
        )

    with open(filepath, "rb") as f:
        files = {"file": f}
        headers = {
            "pinata_api_key": PINATA_API_KEY,
            "pinata_secret_api_key": PINATA_SECRET
        }

        try:
            response = requests.post(PINATA_URL, files=files, headers=headers, timeout=60)
        except requests.RequestException as e:
            raise IPFSUploadError(f"IPFS upload request failed: {e}") from e

    if response.status_code == 200:
        ipfs_hash = response.json()["IpfsHash"]
        return ipfs_hash
    else:
        # Pinata returns JSON error bodies like:
        # {"error": {"reason": "NO_SCOPES_FOUND", "details": "..."}}
        raise IPFSUploadError(
            "IPFS upload failed",
            status_code=response.status_code,
            details=response.text,
        )
