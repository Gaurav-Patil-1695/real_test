"""Unit tests for app.core.security."""
import hashlib
import hmac
from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    compare_token,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("secret")
        assert isinstance(result, str)

    def test_starts_with_bcrypt_prefix(self):
        result = hash_password("secret")
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_different_calls_produce_different_hashes(self):
        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 != h2  # bcrypt uses a random salt

    def test_empty_string(self):
        result = hash_password("")
        assert isinstance(result, str)
        assert len(result) > 0


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_correct(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_empty_password_wrong(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_unicode_password(self):
        pw = "pässwörD123!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True


# ---------------------------------------------------------------------------
# Token hashing (SHA-256)
# ---------------------------------------------------------------------------

class TestHashToken:
    def test_returns_hex_string(self):
        result = hash_token("sometoken")
        # SHA-256 hex digest is 64 characters
        assert isinstance(result, str)
        assert len(result) == 64

    def test_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_matches_stdlib(self):
        token = "my-raw-token"
        expected = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert hash_token(token) == expected

    def test_different_tokens_different_hashes(self):
        assert hash_token("token1") != hash_token("token2")

    def test_empty_token(self):
        result = hash_token("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected


class TestCompareToken:
    def test_correct_token_returns_true(self):
        raw = "rawtoken123"
        stored = hash_token(raw)
        assert compare_token(raw, stored) is True

    def test_wrong_token_returns_false(self):
        stored = hash_token("correcttoken")
        assert compare_token("wrongtoken", stored) is False

    def test_empty_token(self):
        stored = hash_token("")
        assert compare_token("", stored) is True
        assert compare_token("notempty", stored) is False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(subject="42")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_reveals_sub(self):
        token = create_access_token(subject="99")
        payload = decode_access_token(token)
        assert payload["sub"] == "99"

    def test_integer_subject_coerced_to_string(self):
        token = create_access_token(subject=7)
        payload = decode_access_token(token)
        assert payload["sub"] == "7"

    def test_type_claim_is_access(self):
        token = create_access_token(subject="1")
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_extra_claims_included(self):
        token = create_access_token(subject="1", extra_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_custom_expires_delta(self):
        token = create_access_token(subject="1", expires_delta=timedelta(hours=2))
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload
        # exp should be roughly 2h after iat
        diff = payload["exp"] - payload["iat"]
        assert 7100 <= diff <= 7300  # ~7200 seconds

    def test_expired_token_raises(self):
        token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_access_token(token)


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token(subject="42")
        assert isinstance(token, str)

    def test_decode_reveals_sub(self):
        token = create_refresh_token(subject="55")
        payload = decode_refresh_token(token)
        assert payload["sub"] == "55"

    def test_type_claim_is_refresh(self):
        token = create_refresh_token(subject="1")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_integer_subject_coerced_to_string(self):
        token = create_refresh_token(subject=3)
        payload = decode_refresh_token(token)
        assert payload["sub"] == "3"

    def test_custom_expires_delta(self):
        token = create_refresh_token(subject="1", expires_delta=timedelta(days=30))
        payload = decode_refresh_token(token)
        diff = payload["exp"] - payload["iat"]
        assert 2591900 <= diff <= 2592100  # ~30 days in seconds

    def test_expired_token_raises(self):
        token = create_refresh_token(subject="1", expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_refresh_token(token)


class TestDecodeToken:
    def test_valid_access_token(self):
        token = create_access_token(subject="10")
        payload = decode_token(token)
        assert payload["sub"] == "10"

    def test_valid_refresh_token(self):
        token = create_refresh_token(subject="20")
        payload = decode_token(token)
        assert payload["sub"] == "20"

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        token = create_access_token(subject="1")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)


class TestDecodeAccessToken:
    def test_valid_access_token_returns_payload(self):
        token = create_access_token(subject="5")
        payload = decode_access_token(token)
        assert payload["sub"] == "5"
        assert payload["type"] == "access"

    def test_refresh_token_raises(self):
        token = create_refresh_token(subject="5")
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("garbage")


class TestDecodeRefreshToken:
    def test_valid_refresh_token_returns_payload(self):
        token = create_refresh_token(subject="8")
        payload = decode_refresh_token(token)
        assert payload["sub"] == "8"
        assert payload["type"] == "refresh"

    def test_access_token_raises(self):
        token = create_access_token(subject="8")
        with pytest.raises(JWTError):
            decode_refresh_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_refresh_token("garbage")
