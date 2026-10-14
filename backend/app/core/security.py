"""
app/core/security.py
--------------------
Cryptographic utilities for password hashing and JWT token management.
Adheres strictly to PBKDF2-HMAC-SHA256 with 100,000 iterations and salt.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union
from jose import jwt, JWTError
from app.core.config import settings


def hash_password(password: str, salt_hex: Optional[str] = None) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns: {salt}${hash}
    """
    if not salt_hex:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000).hex()
    return f"{salt_hex}${pwd_hash}"


get_password_hash = hash_password


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plain password against the stored {salt}${hash} string.
    """
    if not stored_hash or "$" not in stored_hash:
        return False
    try:
        salt_hex, expected_hash = stored_hash.split("$", 1)
        salt_bytes = bytes.fromhex(salt_hex)
        computed_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt_bytes, 100000).hex()
        return secrets.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def create_access_token(subject: Union[str, int], extra_claims: Optional[Dict[str, Any]] = None, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates an encoded JWT token.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token. Returns payload dict or None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
