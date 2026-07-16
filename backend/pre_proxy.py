import base64
import os
from typing import Tuple

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


def _safe_wallet_filename(wallet_address: str) -> str:
    # keep it filesystem-safe and deterministic
    return (wallet_address or "").strip().lower().replace(":", "_")


def wallet_key_paths(keys_folder: str, wallet_address: str) -> Tuple[str, str]:
    safe = _safe_wallet_filename(wallet_address)
    private_path = os.path.join(keys_folder, f"wallet_{safe}_private.pem")
    public_path = os.path.join(keys_folder, f"wallet_{safe}_public.pem")
    return private_path, public_path


def ensure_wallet_keypair(keys_folder: str, wallet_address: str, bits: int = 2048) -> Tuple[str, str]:
    """Ensure a per-wallet RSA keypair exists on disk; returns (private_path, public_path)."""
    os.makedirs(keys_folder, exist_ok=True)
    private_path, public_path = wallet_key_paths(keys_folder, wallet_address)

    if os.path.exists(private_path) and os.path.exists(public_path):
        return private_path, public_path

    key = RSA.generate(bits)
    with open(private_path, "wb") as f:
        f.write(key.export_key())
    with open(public_path, "wb") as f:
        f.write(key.publickey().export_key())

    return private_path, public_path


def load_public_key_pem(keys_folder: str, wallet_address: str) -> str:
    _, public_path = ensure_wallet_keypair(keys_folder, wallet_address)
    with open(public_path, "rb") as f:
        return f.read().decode("utf-8")


def _load_private_key(keys_folder: str, wallet_address: str) -> RSA.RsaKey:
    private_path, _ = ensure_wallet_keypair(keys_folder, wallet_address)
    with open(private_path, "rb") as f:
        return RSA.import_key(f.read())


def _load_public_key(keys_folder: str, wallet_address: str) -> RSA.RsaKey:
    _, public_path = ensure_wallet_keypair(keys_folder, wallet_address)
    with open(public_path, "rb") as f:
        return RSA.import_key(f.read())


def wrap_key_for_wallet_b64(keys_folder: str, wallet_address: str, raw_key: bytes) -> str:
    """RSA-OAEP wrap; returns base64 string."""
    pub = _load_public_key(keys_folder, wallet_address)
    cipher = PKCS1_OAEP.new(pub)
    wrapped = cipher.encrypt(raw_key)
    return base64.b64encode(wrapped).decode("ascii")


def unwrap_key_for_wallet_b64(keys_folder: str, wallet_address: str, wrapped_b64: str) -> bytes:
    """RSA-OAEP unwrap from base64 string."""
    priv = _load_private_key(keys_folder, wallet_address)
    cipher = PKCS1_OAEP.new(priv)
    wrapped = base64.b64decode((wrapped_b64 or "").encode("ascii"))
    return cipher.decrypt(wrapped)
