"""Unit tests for the reset-password flow (work item: backend-resetPassword).

Tests cover:
  - AuthService.forgotPassword
  - AuthService.resetPassword
  - The /auth/forgot-password and /auth/reset-password HTTP endpoints via TestClient

The in-memory stores in service.py are module-level globals; each test function
resets them to a clean state via the `clean_stores` fixture.
"""
import hashlib
import importlib
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers to reset the in-memory stores between tests
# ---------------------------------------------------------------------------

import app.auth.service as svc_module


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset every in-memory store and counter before each test."""
    svc_module._users.clear()
    svc_module._password_resets.clear()
    svc_module._refresh_tokens.clear()
    svc_module._user_id_counter = 0
    svc_module._pr_id_counter = 0
    svc_module._rt_id_counter = 0
    yield
    svc_module._users.clear()
    svc_module._password_resets.clear()
    svc_module._refresh_tokens.clear()
    svc_module._user_id_counter = 0
    svc_module._pr_id_counter = 0
    svc_module._rt_id_counter = 0


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

def _create_user(email: str = "user@example.com", password: str = "Password1") -> dict:
    """Insert a user directly into the in-memory store and return it."""
    svc_module._user_id_counter += 1
    uid = svc_module._user_id_counter
    now = datetime.now(timezone.utc)
    user = {
        "id": uid,
        "full_name": "Test User",
        "email": email,
        "password_hash": svc_module._hash_password(password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    svc_module._users[uid] = user
    return user


def _create_password_reset(user_id: int, expired: bool = False, used: bool = False) -> tuple[int, str]:
    """Insert a password-reset record and return (pr_id, raw_token)."""
    svc_module._pr_id_counter += 1
    pr_id = svc_module._pr_id_counter
    raw_token = "raw_test_token_" + str(pr_id)
    token_hash = _sha256(raw_token)
    now = datetime.now(timezone.utc)
    expires_at = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    used_at = now if used else None
    svc_module._password_resets[pr_id] = {
        "id": pr_id,
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
        "used_at": used_at,
        "created_at": now,
    }
    return pr_id, raw_token


def _create_refresh_token(user_id: int, revoked: bool = False) -> int:
    """Insert a refresh-token record and return rt_id."""
    svc_module._rt_id_counter += 1
    rt_id = svc_module._rt_id_counter
    now = datetime.now(timezone.utc)
    svc_module._refresh_tokens[rt_id] = {
        "id": rt_id,
        "user_id": user_id,
        "token_hash": _sha256("some_refresh_token_" + str(rt_id)),
        "expires_at": now + timedelta(days=7),
        "revoked_at": now if revoked else None,
        "remember_me": False,
        "created_at": now,
    }
    return rt_id


# ---------------------------------------------------------------------------
# TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from app.main import app  # imported lazily to avoid side-effects at collection
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ============================================================================
# AuthService.forgotPassword – unit tests
# ============================================================================

class TestForgotPassword:
    """Tests for AuthService.forgotPassword."""

    @pytest.mark.asyncio
    async def test_known_email_creates_reset_record(self):
        user = _create_user()
        service = svc_module.AuthService()
        from app.auth.schemas import ForgotPasswordRequest
        body = ForgotPasswordRequest(email=user["email"])
        resp = await service.forgotPassword(body)
        assert resp.message == (
            "If that email is registered, you will receive a"
            " password reset link shortly."
        )
        # A password-reset record should have been created
        assert len(svc_module._password_resets) == 1
        pr = next(iter(svc_module._password_resets.values()))
        assert pr["user_id"] == user["id"]
        assert pr["used_at"] is None
        assert pr["expires_at"] > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_unknown_email_returns_same_message_no_record(self):
        """Must not leak whether the email exists."""
        service = svc_module.AuthService()
        from app.auth.schemas import ForgotPasswordRequest
        body = ForgotPasswordRequest(email="nobody@example.com")
        resp = await service.forgotPassword(body)
        assert resp.message == (
            "If that email is registered, you will receive a"
            " password reset link shortly."
        )
        assert len(svc_module._password_resets) == 0

    @pytest.mark.asyncio
    async def test_token_hash_stored_not_raw(self):
        """The store must hold the SHA-256 hash, not the raw token."""
        user = _create_user()
        service = svc_module.AuthService()
        from app.auth.schemas import ForgotPasswordRequest
        body = ForgotPasswordRequest(email=user["email"])
        await service.forgotPassword(body)
        pr = next(iter(svc_module._password_resets.values()))
        # The token_hash is a 64-char hex string (SHA-256)
        assert len(pr["token_hash"]) == 64
        assert pr["token_hash"].isalnum()

    @pytest.mark.asyncio
    async def test_expiry_is_approximately_one_hour(self):
        user = _create_user()
        service = svc_module.AuthService()
        from app.auth.schemas import ForgotPasswordRequest
        body = ForgotPasswordRequest(email=user["email"])
        before = datetime.now(timezone.utc)
        await service.forgotPassword(body)
        after = datetime.now(timezone.utc)
        pr = next(iter(svc_module._password_resets.values()))
        # expires_at should be within [before+1h, after+1h]
        assert pr["expires_at"] >= before + timedelta(hours=1) - timedelta(seconds=2)
        assert pr["expires_at"] <= after + timedelta(hours=1) + timedelta(seconds=2)


# ============================================================================
# AuthService.resetPassword – unit tests
# ============================================================================

class TestResetPassword:
    """Tests for AuthService.resetPassword."""

    @pytest.mark.asyncio
    async def test_successful_reset(self):
        user = _create_user(password="OldPass1")
        pr_id, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        resp = await service.resetPassword(body)
        assert resp.message == "Your password has been reset successfully."
        # Verify password hash changed
        updated_user = svc_module._users[user["id"]]
        assert svc_module._verify_password("NewPass1", updated_user["password_hash"])
        # Reset record should be marked used
        assert svc_module._password_resets[pr_id]["used_at"] is not None

    @pytest.mark.asyncio
    async def test_reset_revokes_all_refresh_tokens_for_user(self):
        user = _create_user()
        rt_id1 = _create_refresh_token(user["id"])
        rt_id2 = _create_refresh_token(user["id"])
        pr_id, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        await service.resetPassword(body)
        assert svc_module._refresh_tokens[rt_id1]["revoked_at"] is not None
        assert svc_module._refresh_tokens[rt_id2]["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_reset_does_not_revoke_other_user_refresh_tokens(self):
        user1 = _create_user(email="u1@example.com")
        user2 = _create_user(email="u2@example.com")
        rt_id_other = _create_refresh_token(user2["id"])
        pr_id, raw_token = _create_password_reset(user1["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        await service.resetPassword(body)
        # Other user's token must NOT be revoked
        assert svc_module._refresh_tokens[rt_id_other]["revoked_at"] is None

    @pytest.mark.asyncio
    async def test_reset_password_mismatch_raises_422(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="DifferentPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_reset_weak_password_raises_422(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="weak",
            confirm_password="weak",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_invalid_token_raises_400(self):
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token="does_not_exist",
            password="NewPass1",
            confirm_password="NewPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_expired_token_raises_400(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"], expired=True)
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_already_used_token_raises_400(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"], used=True)
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_token_cannot_be_reused(self):
        """After a successful reset the token is marked used; a second attempt must fail."""
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest

        body1 = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        await service.resetPassword(body1)

        body2 = ResetPasswordRequest(
            token=raw_token,
            password="AnotherPass1",
            confirm_password="AnotherPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body2)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_with_password_missing_uppercase_raises_422(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="lowercase1",
            confirm_password="lowercase1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_with_password_missing_digit_raises_422(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NoDigitHere",
            confirm_password="NoDigitHere",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_with_password_too_short_raises_422(self):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="Ab1",
            confirm_password="Ab1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_updates_user_updated_at(self):
        user = _create_user()
        original_updated_at = user["updated_at"]
        _, raw_token = _create_password_reset(user["id"])
        service = svc_module.AuthService()
        from app.auth.schemas import ResetPasswordRequest
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1",
            confirm_password="NewPass1",
        )
        await service.resetPassword(body)
        updated_user = svc_module._users[user["id"]]
        assert updated_user["updated_at"] >= original_updated_at


# ============================================================================
# HTTP endpoint tests via TestClient
# ============================================================================

class TestForgotPasswordEndpoint:
    def test_known_email_returns_202(self, client):
        _create_user(email="test@example.com")
        resp = client.post("/auth/forgot-password", json={"email": "test@example.com"})
        assert resp.status_code == 202
        data = resp.json()
        assert "message" in data
        assert "password reset link" in data["message"].lower() or "registered" in data["message"].lower()

    def test_unknown_email_returns_202_same_body(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
        assert resp.status_code == 202
        data = resp.json()
        assert "message" in data

    def test_invalid_email_format_returns_422(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "not-an-email"})
        assert resp.status_code == 422

    def test_missing_email_field_returns_422(self, client):
        resp = client.post("/auth/forgot-password", json={})
        assert resp.status_code == 422


class TestResetPasswordEndpoint:
    def test_valid_reset_returns_200(self, client):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "reset successfully" in data["message"].lower()

    def test_password_mismatch_returns_422(self, client):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPass1",
                "confirmPassword": "DifferentPass1",
            },
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "PASSWORD_MISMATCH"

    def test_invalid_token_returns_400(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "invalidtoken",
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    def test_expired_token_returns_400(self, client):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"], expired=True)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    def test_already_used_token_returns_400(self, client):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"], used=True)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    def test_weak_password_returns_422(self, client):
        user = _create_user()
        _, raw_token = _create_password_reset(user["id"])
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "weak",
                "confirmPassword": "weak",
            },
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["error"]["code"] == "WEAK_PASSWORD"

    def test_missing_token_field_returns_422(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 422

    def test_missing_password_field_returns_422(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "sometoken",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 422

    def test_reset_revokes_refresh_tokens_visible_via_login(self, client):
        """After reset, old refresh tokens are revoked (store check)."""
        user = _create_user()
        rt_id = _create_refresh_token(user["id"])
        _, raw_token = _create_password_reset(user["id"])
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPass1",
                "confirmPassword": "NewPass1",
            },
        )
        assert resp.status_code == 200
        assert svc_module._refresh_tokens[rt_id]["revoked_at"] is not None
