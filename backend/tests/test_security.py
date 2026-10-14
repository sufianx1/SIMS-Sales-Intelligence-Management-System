"""
backend/tests/test_security.py
------------------------------
Unit tests for password hashing and JWT token management.
"""

from datetime import timedelta
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    raw_password = "SecretPassword123!"
    hashed = hash_password(raw_password)

    assert "$" in hashed
    salt, hash_val = hashed.split("$", 1)
    assert len(salt) == 32  # 16 bytes in hex
    assert len(hash_val) == 64  # SHA-256 is 32 bytes in hex

    # Verify correct password
    assert verify_password(raw_password, hashed) is True

    # Verify incorrect password
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = 1002
    claims = {"email": "shehzad@sms.example", "is_system_admin": True}
    token = create_access_token(subject=user_id, extra_claims=claims, expires_delta=timedelta(minutes=15))

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "shehzad@sms.example"
    assert payload["is_system_admin"] is True
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_or_invalid_token():
    # Expired token
    expired_token = create_access_token(
        subject=999,
        expires_delta=timedelta(seconds=-1)
    )
    assert decode_access_token(expired_token) is None

    # Corrupted token
    assert decode_access_token("not-a-valid-token-string") is None
