from Crypto.Cipher import AES, ChaCha20
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES as _AES
from Crypto.Random import get_random_bytes
from Crypto.Random import get_random_bytes as _get_random_bytes
import os

# AES-GCM Encryption
def encrypt_aes(file_data):
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(file_data)
    
    return {
        "ciphertext": ciphertext,
        "key": key,
        "nonce": cipher.nonce,
        "tag": tag
    }

# AES-GCM Decryption
def decrypt_aes(enc_data):
    cipher = AES.new(enc_data["key"], AES.MODE_GCM, nonce=enc_data["nonce"])
    return cipher.decrypt_and_verify(enc_data["ciphertext"], enc_data["tag"])


# ChaCha20 Encryption
def encrypt_chacha(file_data):
    key = get_random_bytes(32)
    cipher = ChaCha20.new(key=key)
    ciphertext = cipher.encrypt(file_data)

    return {
        "ciphertext": ciphertext,
        "key": key,
        "nonce": cipher.nonce
    }

# ChaCha20 Decryption
def decrypt_chacha(enc_data):
    cipher = ChaCha20.new(key=enc_data["key"], nonce=enc_data["nonce"])
    return cipher.decrypt(enc_data["ciphertext"])


def generate_rsa_keypair(bits: int = 2048):
    """Returns (private_key_pem_str, public_key_pem_str)"""
    key = RSA.generate(bits)
    return key.export_key().decode(), key.publickey().export_key().decode()


def encrypt_rsa(data: bytes, public_key_pem: str) -> bytes:
    """
    RSA hybrid encryption:
    1. Generate random 32-byte AES session key
    2. Encrypt session key with RSA-OAEP (2048-bit)
    3. Encrypt data with AES-GCM using session key
    Format: [2 bytes rsa_len][rsa_encrypted_key][16 nonce][16 tag][ciphertext]
    """
    session_key = _get_random_bytes(32)
    rsa_key = RSA.import_key(public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(rsa_key)
    encrypted_session_key = cipher_rsa.encrypt(session_key)

    cipher_aes = _AES.new(session_key, _AES.MODE_GCM)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data)

    rsa_len = len(encrypted_session_key).to_bytes(2, "big")
    return rsa_len + encrypted_session_key + cipher_aes.nonce + tag + ciphertext


def decrypt_rsa(enc_data: bytes, private_key_pem: str) -> bytes:
    """Reverse of encrypt_rsa"""
    rsa_len = int.from_bytes(enc_data[:2], "big")
    encrypted_session_key = enc_data[2 : 2 + rsa_len]
    rest = enc_data[2 + rsa_len :]
    nonce = rest[:16]
    tag = rest[16:32]
    ciphertext = rest[32:]

    rsa_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(rsa_key)
    session_key = cipher_rsa.decrypt(encrypted_session_key)

    cipher_aes = _AES.new(session_key, _AES.MODE_GCM, nonce=nonce)
    return cipher_aes.decrypt_and_verify(ciphertext, tag)