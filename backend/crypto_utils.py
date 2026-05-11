from Crypto.Cipher import AES, ChaCha20
from Crypto.Random import get_random_bytes
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