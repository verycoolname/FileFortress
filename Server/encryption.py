import bcrypt
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

def get_key():
    return b'Shalom1Vanunu123'

def encrypt_email(email):
    # Ensure email length is a multiple of block size (16 bytes)
    cipher = AES.new(get_key(), AES.MODE_ECB)  # ECB mode for deterministic encryption
    padded_email = pad(email.encode(), AES.block_size)  # Padding the email to block size
    encrypted_email = cipher.encrypt(padded_email)
    return encrypted_email.hex()  # Return as hex string to store

def decrypt_email(encrypted_email):
    cipher = AES.new(get_key(), AES.MODE_ECB)
    encrypted_email_bytes = bytes.fromhex(encrypted_email)
    decrypted_email = unpad(cipher.decrypt(encrypted_email_bytes), AES.block_size)
    return decrypted_email.decode()

def encrypt_data(data: bytes) -> bytes:
    cipher = AES.new(get_key(), AES.MODE_ECB)  # ECB mode (not recommended for security)
    padded_data = pad(data, AES.block_size)  # Pad the binary data

    return cipher.encrypt(padded_data)  # Return raw encrypted bytes

def decrypt_data(encrypted_data: bytes) -> bytes:
    cipher = AES.new(get_key(), AES.MODE_ECB)  # Use the same key and mode
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)  # Decrypt and unpad
    return decrypted_data  # Return raw decrypted bytes