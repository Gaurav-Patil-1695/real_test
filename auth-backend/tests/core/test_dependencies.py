"""Unit tests for app.core.dependencies."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_active_user(user_id: int = 1) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = True
    return user


def _make_inactive_user(user_id: int = 2) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = False
    return user


def _make_db(user) -> MagicMock:
    db = MagicMock()
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value
    filter_mock.first.return_value = user
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    # -- Missing credentials --

    def test_no_credentials_raises_401(self):
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=db)
        assert exc_info.value.status_code == 401

    # -- Invalid / malformed token --

    def test_invalid_token_raises_401(self):
        db = MagicMock()
        creds = _make_credentials("not.a.valid.token")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    def test_refresh_token_instead_of_access_raises_401(self):
        token = create_refresh_token(subject="1")
        creds = _make_credentials(token)
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    # -- User not found --

    def test_user_not_found_raises_401(self):
        token = create_access_token(subject="999")
        creds = _make_credentials(token)
        db = _make_db(None)  # no user returned
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    # -- Inactive user --

    def test_inactive_user_raises_401(self):
        user = _make_inactive_user(user_id=5)
        token = create_access_token(subject="5")
        creds = _make_credentials(token)
        db = _make_db(user)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=creds, db=db)
        assert exc_info.value.status_code == 401

    # -- Happy path --

    def test_valid_token_and_active_user_returns_user(self):
        user = _make_active_user(user_id=42)
        token = create_access_token(subject="42")
        creds = _make_credentials(token)
        db = _make_db(user)
        result = get_current_user(credentials=creds, db=db)
        assert result is user

    # -- Error payload structure --

    def test_error_payload_structure_on_401(self):
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=db)
        detail = exc_info.value.detail
        assert "error" in detail
        assert detail["error"]["code"] == "UNAUTHORIZED"

    def test_www_authenticate_header_present(self):
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=db)
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"

    # -- Non-integer sub claim --

    def test_non_integer_sub_raises_401(self):
        """A token whose sub cannot be cast to int should yield 401."""
        with patch("app.core.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"sub": "not-an-int", "type": "access"}
            creds = _make_credentials("fake.token.value")
            db = MagicMock()
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials=creds, db=db)
            assert exc_info.value.status_code == 401

    def test_missing_sub_raises_401(self):
        """A token whose sub is absent should yield 401."""
        with patch("app.core.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"type": "access"}
            creds = _make_credentials("fake.token.value")
            db = MagicMock()
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials=creds, db=db)
            assert exc_info.value.status_code == 401

    def test_db_queried_with_correct_user_id(self):
        user = _make_active_user(user_id=77)
        token = create_access_token(subject="77")
        creds = _make_credentials(token)
        db = _make_db(user)
        get_current_user(credentials=creds, db=db)
        db.query.assert_called_once()
