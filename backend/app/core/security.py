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
    Creates an encoded JWT token with unique jti claim.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "jti": secrets.token_hex(16),
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
    Rejects revoked tokens.
    """
    try:
        if is_token_revoked(token):
            return None
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def revoke_token(token: str):
    """
    Blacklists a JWT token until its natural expiration.
    """
    from app.db.mongo import get_db
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        exp_ts = payload.get("exp")
        if exp_ts:
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    except Exception:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    db = get_db()
    db.revoked_tokens.update_one(
        {"token": token},
        {"$set": {"token": token, "revoked_at": datetime.now(timezone.utc), "expires_at": expires_at}},
        upsert=True
    )


def is_token_revoked(token: str) -> bool:
    """
    Checks if a token has been explicitly revoked / blacklisted.
    """
    from app.db.mongo import get_db
    try:
        db = get_db()
        return db.revoked_tokens.find_one({"token": token}) is not None
    except Exception:
        return False


def check_login_rate_limit(identifier: str, ip_address: Optional[str] = None) -> bool:
    """
    Checks whether login attempts have exceeded the brute-force threshold.
    Returns True if allowed, False if locked out.
    """
    from app.db.mongo import get_db
    try:
        db = get_db()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        query: Dict[str, Any] = {
            "identifier": identifier.strip().lower(),
            "success": False,
            "timestamp": {"$gte": cutoff}
        }
        recent_failures = db.login_attempts.count_documents(query)
        return recent_failures < settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS
    except Exception:
        return True


def record_login_attempt(identifier: str, ip_address: Optional[str] = None, success: bool = False):
    """
    Records a login attempt for audit and rate-limiting purposes.
    """
    from app.db.mongo import get_db
    try:
        db = get_db()
        now = datetime.now(timezone.utc)
        db.login_attempts.insert_one({
            "identifier": identifier.strip().lower(),
            "ip_address": ip_address or "unknown",
            "success": success,
            "timestamp": now
        })
    except Exception:
        pass


def sanitize_for_csv(val: Any) -> Any:
    """
    Prevents CSV Formula Injection (DDE) by neutralizing leading dangerous characters
    (=, +, -, @, tab, newline, carriage return).
    """
    if val is None:
        return ""
    if not isinstance(val, str):
        return val
    cleaned = val.lstrip(" ")
    if cleaned and cleaned[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return f"'{val}"
    return val


def verify_webhook_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """
    Verifies HMAC-SHA256 signature with constant-time comparison to prevent timing attacks.
    """
    import hmac
    if not signature_header or not secret:
        return False
    # Strip prefix like 'sha256=' if present
    expected_sig = signature_header
    if "=" in signature_header:
        expected_sig = signature_header.split("=", 1)[1]

    computed_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return secrets.compare_digest(computed_sig.lower(), expected_sig.lower())
