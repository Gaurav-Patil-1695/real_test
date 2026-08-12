"""Unit tests for app.auth.repository — all DB I/O is mocked."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers to build fake row objects that mimic SQLAlchemy Row._mapping
# ---------------------------------------------------------------------------

class FakeRow:
    """Mimics a SQLAlchemy Row with a _mapping attribute."""
    def __init__(self, data: dict):
        self._mapping = data


class FakeResult:
    """Mimics the result returned by conn.execute()."""
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


def make_conn(row=None):
    """Return an AsyncMock connection whose execute() returns FakeResult(row)."""
    conn = AsyncMock()
    conn.execute.return_value = FakeResult(row)
    return conn


# ---------------------------------------------------------------------------
# Import the module under test after helpers are defined
# ---------------------------------------------------------------------------

from app.auth.repository import (
    _row_to_user,
    get_user_by_id,
    get_user_by_email,
    create_user,
    update_user_password,
    create_password_reset,
    get_password_reset_by_token_hash,
    mark_password_reset_used,
    invalidate_previous_password_resets,
    create_refresh_token,
    get_refresh_token_by_token_hash,
    revoke_refresh_token,
    revoke_all_refresh_tokens_for_user,
)


# ===========================================================================
# _row_to_user
# ===========================================================================

class TestRowToUser:
    def test_returns_none_for_none(self):
        assert _row_to_user(None) is None

    def test_converts_row_to_dict(self):
        data = {"id": 1, "email": "a@b.com", "full_name": "Alice"}
        row = FakeRow(data)
        result = _row_to_user(row)
        assert result == data
        assert isinstance(result, dict)


# ===========================================================================
# get_user_by_id
# ===========================================================================

class TestGetUserById:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self):
        user_data = {"id": 42, "email": "user@example.com", "full_name": "Bob",
                     "password_hash": "hash", "is_active": True,
                     "created_at": None, "updated_at": None}
        conn = make_conn(FakeRow(user_data))
        result = await get_user_by_id(conn, 42)
        assert result == user_data
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = make_conn(None)
        result = await get_user_by_id(conn, 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_id(self):
        conn = make_conn(None)
        await get_user_by_id(conn, 7)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"id": 7}


# ===========================================================================
# get_user_by_email
# ===========================================================================

class TestGetUserByEmail:
    @pytest.mark.asyncio
    async def test_returns_user_when_found(self):
        user_data = {"id": 1, "email": "alice@example.com", "full_name": "Alice",
                     "password_hash": "h", "is_active": True,
                     "created_at": None, "updated_at": None}
        conn = make_conn(FakeRow(user_data))
        result = await get_user_by_email(conn, "alice@example.com")
        assert result == user_data

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = make_conn(None)
        result = await get_user_by_email(conn, "nobody@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_email(self):
        conn = make_conn(None)
        await get_user_by_email(conn, "test@test.com")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"email": "test@test.com"}


# ===========================================================================
# create_user
# ===========================================================================

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_returns_created_user_dict(self):
        user_data = {"id": 10, "full_name": "Carol", "email": "carol@example.com",
                     "password_hash": "phash", "is_active": True,
                     "created_at": None, "updated_at": None}
        conn = make_conn(FakeRow(user_data))
        result = await create_user(conn, "Carol", "carol@example.com", "phash")
        assert result == user_data

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        user_data = {"id": 11, "full_name": "Dave", "email": "dave@example.com",
                     "password_hash": "pw", "is_active": True,
                     "created_at": None, "updated_at": None}
        conn = make_conn(FakeRow(user_data))
        await create_user(conn, "Dave", "dave@example.com", "pw")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"full_name": "Dave", "email": "dave@example.com",
                          "password_hash": "pw"}


# ===========================================================================
# update_user_password
# ===========================================================================

class TestUpdateUserPassword:
    @pytest.mark.asyncio
    async def test_executes_update(self):
        conn = make_conn()
        await update_user_password(conn, 5, "newhash")
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        conn = make_conn()
        await update_user_password(conn, 5, "newhash")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"password_hash": "newhash", "id": 5}


# ===========================================================================
# create_password_reset
# ===========================================================================

class TestCreatePasswordReset:
    @pytest.mark.asyncio
    async def test_returns_reset_dict(self):
        expires = datetime(2099, 1, 1, tzinfo=timezone.utc)
        reset_data = {"id": 1, "user_id": 3, "token_hash": "th",
                      "expires_at": expires, "used_at": None, "created_at": None}
        conn = make_conn(FakeRow(reset_data))
        result = await create_password_reset(conn, 3, "th", expires)
        assert result == reset_data

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        expires = datetime(2099, 1, 1, tzinfo=timezone.utc)
        reset_data = {"id": 1, "user_id": 3, "token_hash": "th",
                      "expires_at": expires, "used_at": None, "created_at": None}
        conn = make_conn(FakeRow(reset_data))
        await create_password_reset(conn, 3, "th", expires)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"user_id": 3, "token_hash": "th", "expires_at": expires}


# ===========================================================================
# get_password_reset_by_token_hash
# ===========================================================================

class TestGetPasswordResetByTokenHash:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        expires = datetime(2099, 1, 1, tzinfo=timezone.utc)
        reset_data = {"id": 2, "user_id": 4, "token_hash": "abc",
                      "expires_at": expires, "used_at": None, "created_at": None}
        conn = make_conn(FakeRow(reset_data))
        result = await get_password_reset_by_token_hash(conn, "abc")
        assert result == reset_data

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = make_conn(None)
        result = await get_password_reset_by_token_hash(conn, "missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_token_hash(self):
        conn = make_conn(None)
        await get_password_reset_by_token_hash(conn, "myhash")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"token_hash": "myhash"}


# ===========================================================================
# mark_password_reset_used
# ===========================================================================

class TestMarkPasswordResetUsed:
    @pytest.mark.asyncio
    async def test_executes_update(self):
        conn = make_conn()
        await mark_password_reset_used(conn, 99)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_id(self):
        conn = make_conn()
        await mark_password_reset_used(conn, 99)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"id": 99}


# ===========================================================================
# invalidate_previous_password_resets
# ===========================================================================

class TestInvalidatePreviousPasswordResets:
    @pytest.mark.asyncio
    async def test_executes_update(self):
        conn = make_conn()
        await invalidate_previous_password_resets(conn, 7)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_user_id(self):
        conn = make_conn()
        await invalidate_previous_password_resets(conn, 7)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"user_id": 7}


# ===========================================================================
# create_refresh_token
# ===========================================================================

class TestCreateRefreshToken:
    @pytest.mark.asyncio
    async def test_returns_token_dict(self):
        expires = datetime(2099, 6, 1, tzinfo=timezone.utc)
        token_data = {"id": 1, "user_id": 5, "token_hash": "rth",
                      "expires_at": expires, "revoked_at": None,
                      "remember_me": False, "created_at": None}
        conn = make_conn(FakeRow(token_data))
        result = await create_refresh_token(conn, 5, "rth", expires, False)
        assert result == token_data

    @pytest.mark.asyncio
    async def test_passes_correct_params(self):
        expires = datetime(2099, 6, 1, tzinfo=timezone.utc)
        token_data = {"id": 1, "user_id": 5, "token_hash": "rth",
                      "expires_at": expires, "revoked_at": None,
                      "remember_me": True, "created_at": None}
        conn = make_conn(FakeRow(token_data))
        await create_refresh_token(conn, 5, "rth", expires, True)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"user_id": 5, "token_hash": "rth",
                          "expires_at": expires, "remember_me": True}


# ===========================================================================
# get_refresh_token_by_token_hash
# ===========================================================================

class TestGetRefreshTokenByTokenHash:
    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        expires = datetime(2099, 6, 1, tzinfo=timezone.utc)
        token_data = {"id": 1, "user_id": 5, "token_hash": "rth",
                      "expires_at": expires, "revoked_at": None,
                      "remember_me": False, "created_at": None}
        conn = make_conn(FakeRow(token_data))
        result = await get_refresh_token_by_token_hash(conn, "rth")
        assert result == token_data

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        conn = make_conn(None)
        result = await get_refresh_token_by_token_hash(conn, "ghost")
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_token_hash(self):
        conn = make_conn(None)
        await get_refresh_token_by_token_hash(conn, "xhash")
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"token_hash": "xhash"}


# ===========================================================================
# revoke_refresh_token
# ===========================================================================

class TestRevokeRefreshToken:
    @pytest.mark.asyncio
    async def test_executes_update(self):
        conn = make_conn()
        await revoke_refresh_token(conn, 123)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_id(self):
        conn = make_conn()
        await revoke_refresh_token(conn, 123)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"id": 123}


# ===========================================================================
# revoke_all_refresh_tokens_for_user
# ===========================================================================

class TestRevokeAllRefreshTokensForUser:
    @pytest.mark.asyncio
    async def test_executes_update(self):
        conn = make_conn()
        await revoke_all_refresh_tokens_for_user(conn, 8)
        conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_passes_correct_user_id(self):
        conn = make_conn()
        await revoke_all_refresh_tokens_for_user(conn, 8)
        call_args = conn.execute.call_args
        params = call_args[0][1]
        assert params == {"user_id": 8}
