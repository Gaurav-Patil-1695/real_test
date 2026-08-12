"""Unit tests for app.auth.tokens."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.auth.tokens import (
    hash_token,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    is_refresh_token_valid,
    rotate_refresh_token,
    create_reset_token,
    is_reset_token_valid,
    ACCESS_TOKEN_TTL,
    REFRESH_TOKEN_TTL_DEFAULT,
    REFRESH_TOKEN_TTL_EXTENDED,
    RESET_TOKEN_TTL,
)


# ===========================================================================
# hash_token
# ===========================================================================

class TestHashToken:
    def test_returns_sha256_hex(self):
        token = "hello"
        expected = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert hash_token(token) == expected

    def test_deterministic(self):
        assert hash_token("abc") == hash_token("abc")

    def test_different_tokens_different_hashes(self):
        assert hash_token("foo") != hash_token("bar")

    def test_returns_64_char_hex_string(self):
        result = hash_token("some_token")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


# ===========================================================================
# create_access_token / decode_access_token
# ===========================================================================

class TestAccessToken:
    def test_create_returns_string(self):
        token = create_access_token(1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        token = create_access_token(42)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_decode_invalid_token_returns_none(self):
        assert decode_access_token("not.a.token") is None

    def test_decode_tampered_token_returns_none(self):
        token = create_access_token(1)
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_decode_wrong_type_returns_none(self):
        """A JWT with type != 'access' should return None."""
        from jose import jwt
        from app.config.settings import settings
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": "1",
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "type": "refresh",  # wrong type
        }
        bad_token = jwt.encode(payload, settings.SECRET_KEY,
                               algorithm=settings.JWT_ALGORITHM)
        assert decode_access_token(bad_token) is None

    def test_decode_expired_token_returns_none(self):
        from jose import jwt
        from app.config.settings import settings
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": "1",
            "exp": now - timedelta(seconds=1),  # already expired
            "iat": now - timedelta(minutes=1),
            "type": "access",
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY,
                                   algorithm=settings.JWT_ALGORITHM)
        assert decode_access_token(expired_token) is None

    def test_sub_is_string_of_user_id(self):
        payload = decode_access_token(create_access_token(99))
        assert payload["sub"] == "99"


# ===========================================================================
# create_refresh_token
# ===========================================================================

class TestCreateRefreshToken:
    def test_returns_three_tuple(self):
        result = create_refresh_token()
        assert len(result) == 3

    def test_raw_token_is_string(self):
        raw, _, _ = create_refresh_token()
        assert isinstance(raw, str)
        assert len(raw) > 0

    def test_token_hash_matches_raw(self):
        raw, token_hash, _ = create_refresh_token()
        assert token_hash == hash_token(raw)

    def test_expires_at_is_aware_datetime(self):
        _, _, expires_at = create_refresh_token()
        assert isinstance(expires_at, datetime)
        assert expires_at.tzinfo is not None

    def test_default_ttl(self):
        now = datetime.now(tz=timezone.utc)
        _, _, expires_at = create_refresh_token(remember_me=False)
        diff = expires_at - now
        # Should be within a few seconds of REFRESH_TOKEN_TTL_DEFAULT
        assert abs(diff.total_seconds() - REFRESH_TOKEN_TTL_DEFAULT.total_seconds()) < 5

    def test_remember_me_ttl(self):
        now = datetime.now(tz=timezone.utc)
        _, _, expires_at = create_refresh_token(remember_me=True)
        diff = expires_at - now
        assert abs(diff.total_seconds() - REFRESH_TOKEN_TTL_EXTENDED.total_seconds()) < 5

    def test_raw_tokens_are_unique(self):
        raw1, _, _ = create_refresh_token()
        raw2, _, _ = create_refresh_token()
        assert raw1 != raw2


# ===========================================================================
# is_refresh_token_valid
# ===========================================================================

class TestIsRefreshTokenValid:
    def _future(self):
        return datetime.now(tz=timezone.utc) + timedelta(hours=1)

    def _past(self):
        return datetime.now(tz=timezone.utc) - timedelta(seconds=1)

    def test_valid_token(self):
        row = {"revoked_at": None, "expires_at": self._future()}
        assert is_refresh_token_valid(row) is True

    def test_revoked_token(self):
        row = {"revoked_at": datetime.now(tz=timezone.utc), "expires_at": self._future()}
        assert is_refresh_token_valid(row) is False

    def test_expired_token(self):
        row = {"revoked_at": None, "expires_at": self._past()}
        assert is_refresh_token_valid(row) is False

    def test_expired_and_revoked(self):
        row = {"revoked_at": datetime.now(tz=timezone.utc), "expires_at": self._past()}
        assert is_refresh_token_valid(row) is False

    def test_naive_expires_at_treated_as_utc(self):
        # naive datetime that is in the future
        future_naive = datetime.now() + timedelta(hours=1)
        row = {"revoked_at": None, "expires_at": future_naive}
        assert is_refresh_token_valid(row) is True

    def test_naive_expires_at_past_treated_as_expired(self):
        past_naive = datetime.now() - timedelta(seconds=1)
        row = {"revoked_at": None, "expires_at": past_naive}
        assert is_refresh_token_valid(row) is False


# ===========================================================================
# rotate_refresh_token
# ===========================================================================

class TestRotateRefreshToken:
    def test_returns_three_tuple(self):
        old_row = {"remember_me": False,
                   "expires_at": datetime.now(tz=timezone.utc) + timedelta(hours=1)}
        result = rotate_refresh_token(old_row)
        assert len(result) == 3

    def test_preserves_remember_me_false(self):
        old_row = {"remember_me": False,
                   "expires_at": datetime.now(tz=timezone.utc) + timedelta(hours=1)}
        _, _, expires_at = rotate_refresh_token(old_row)
        expected_ttl = REFRESH_TOKEN_TTL_DEFAULT.total_seconds()
        diff = (expires_at - datetime.now(tz=timezone.utc)).total_seconds()
        assert abs(diff - expected_ttl) < 5

    def test_preserves_remember_me_true(self):
        old_row = {"remember_me": True,
                   "expires_at": datetime.now(tz=timezone.utc) + timedelta(hours=1)}
        _, _, expires_at = rotate_refresh_token(old_row)
        expected_ttl = REFRESH_TOKEN_TTL_EXTENDED.total_seconds()
        diff = (expires_at - datetime.now(tz=timezone.utc)).total_seconds()
        assert abs(diff - expected_ttl) < 5

    def test_new_raw_token_differs_from_old(self):
        old_row = {"remember_me": False,
                   "expires_at": datetime.now(tz=timezone.utc) + timedelta(hours=1),
                   "token_hash": "oldhash"}
        raw, token_hash, _ = rotate_refresh_token(old_row)
        assert hash_token(raw) == token_hash
        assert token_hash != "oldhash"

    def test_missing_remember_me_defaults_to_false(self):
        old_row = {"expires_at": datetime.now(tz=timezone.utc) + timedelta(hours=1)}
        _, _, expires_at = rotate_refresh_token(old_row)
        diff = (expires_at - datetime.now(tz=timezone.utc)).total_seconds()
        assert abs(diff - REFRESH_TOKEN_TTL_DEFAULT.total_seconds()) < 5


# ===========================================================================
# create_reset_token
# ===========================================================================

class TestCreateResetToken:
    def test_returns_three_tuple(self):
        result = create_reset_token()
        assert len(result) == 3

    def test_raw_token_is_string(self):
        raw, _, _ = create_reset_token()
        assert isinstance(raw, str)
        assert len(raw) > 0

    def test_hash_matches_raw(self):
        raw, token_hash, _ = create_reset_token()
        assert token_hash == hash_token(raw)

    def test_expires_at_is_aware_datetime(self):
        _, _, expires_at = create_reset_token()
        assert isinstance(expires_at, datetime)
        assert expires_at.tzinfo is not None

    def test_ttl_matches_settings(self):
        now = datetime.now(tz=timezone.utc)
        _, _, expires_at = create_reset_token()
        diff = expires_at - now
        assert abs(diff.total_seconds() - RESET_TOKEN_TTL.total_seconds()) < 5

    def test_tokens_are_unique(self):
        raw1, _, _ = create_reset_token()
        raw2, _, _ = create_reset_token()
        assert raw1 != raw2


# ===========================================================================
# is_reset_token_valid
# ===========================================================================

class TestIsResetTokenValid:
    def _future(self):
        return datetime.now(tz=timezone.utc) + timedelta(hours=1)

    def _past(self):
        return datetime.now(tz=timezone.utc) - timedelta(seconds=1)

    def test_valid_token(self):
        row = {"used_at": None, "expires_at": self._future()}
        assert is_reset_token_valid(row) is True

    def test_used_token(self):
        row = {"used_at": datetime.now(tz=timezone.utc), "expires_at": self._future()}
        assert is_reset_token_valid(row) is False

    def test_expired_token(self):
        row = {"used_at": None, "expires_at": self._past()}
        assert is_reset_token_valid(row) is False

    def test_used_and_expired(self):
        row = {"used_at": datetime.now(tz=timezone.utc), "expires_at": self._past()}
        assert is_reset_token_valid(row) is False

    def test_naive_future_expires_at(self):
        future_naive = datetime.now() + timedelta(hours=1)
        row = {"used_at": None, "expires_at": future_naive}
        assert is_reset_token_valid(row) is True

    def test_naive_past_expires_at(self):
        past_naive = datetime.now() - timedelta(seconds=1)
        row = {"used_at": None, "expires_at": past_naive}
        assert is_reset_token_valid(row) is False
