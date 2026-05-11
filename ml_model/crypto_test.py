from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

data = b"Hello World"
encrypted = cipher.encrypt(data)

print("Encrypted:", encrypted)