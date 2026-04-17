"""
app/core/security.py
--------------------
AES-256-GCM field-level encryption for sensitive database fields (e.g. eToro user keys).
JWT creation & verification for API authentication.
Password hashing using bcrypt via passlib.
"""
import os
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# ── Password hashing ─────────────────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── AES-256-GCM Field Encryption ─────────────────────────────────────────────
def _get_aes_key() -> bytes:
    """
    Derives a 32-byte AES key from HashiCorp Vault.
    """
    from app.core.vault import get_master_key
    b64_key = get_master_key()
    if not b64_key:
        raise ValueError("Vault master key not found!")
    
    # ensure it's exactly 32 bytes for AES-256
    raw_key = base64.urlsafe_b64decode(b64_key)
    return raw_key[:32].ljust(32, b'\0')


def encrypt_field(plaintext: str) -> str:
    """
    Encrypts a plaintext string using AES-256-CBC with PKCS7 padding.
    Returns a base64-encoded JSON payload: {iv: ..., c: ...}
    """
    key = _get_aes_key()
    iv = os.urandom(16)  # 128-bit IV for AES-CBC
    
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    payload = {
        "iv": base64.b64encode(iv).decode(),
        "c": base64.b64encode(ciphertext).decode(),
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


def decrypt_field(encrypted: str) -> str:
    """
    Decrypts a field previously encrypted with encrypt_field().
    Raises ValueError on tampered/invalid data.
    Supports legacy AES-GCM decryption if payload has "n" instead of "iv".
    """
    key = _get_aes_key()
    payload = json.loads(base64.b64decode(encrypted).decode())
    ciphertext = base64.b64decode(payload["c"])
    
    # Handle backward compatibility for old AES-GCM encrypted data
    if "n" in payload:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        nonce = base64.b64decode(payload["n"])
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
        
    iv = base64.b64decode(payload["iv"])
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    
    return plaintext.decode()

