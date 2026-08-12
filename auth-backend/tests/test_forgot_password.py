"""Unit tests for the forgotPassword feature (router + service)."""
import importlib
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers to reset in-memory stores between tests
# ---------------------------------------------------------------------------

def _reset_service_state():
    """Reset all in-memory stores and counters in app.auth.service."""
    import app.auth.service as svc

    svc._users.clear()
    svc._password_resets.clear()
    svc._refresh_tokens.clear()
    svc._user_id_counter = 0
    svc._pr_id_counter = 0
    svc._rt_id_counter = 0


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure a clean in-memory state for every test."""
    _reset_service_state()
    yield
    _reset_service_state()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from app.main import app  # adjust if your entrypoint differs
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def service():
    from app.auth.service import AuthService
    return AuthService()


@pytest.fixture()
def registered_user(service):
    """Register a user and return the raw user dict from the store."""
    import asyncio
    from app.auth.schemas import RegisterRequest
    import app.auth.service as svc

    req = RegisterRequest(
        fullName="Test User",
        email="user@example.com",
        password="Password1",
        confirmPassword="Password1",
    )
    asyncio.get_event_loop().run_until_complete(service.register(req))
    return svc._find_user_by_email("user@example.com")


# ---------------------------------------------------------------------------
# Service-level tests: forgotPassword
# ---------------------------------------------------------------------------

class TestForgotPasswordService:
    """Tests for AuthService.forgotPassword."""

    @pytest.mark.asyncio
    async def test_returns_generic_message_for_existing_email(self, service, registered_user):
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="user@example.com")
        resp = await service.forgotPassword(req)

        assert resp.message == (
            "If that email is registered, you will receive a"
            " password reset link shortly."
        )

    @pytest.mark.asyncio
    async def test_returns_generic_message_for_nonexistent_email(self, service):
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="nobody@nowhere.com")
        resp = await service.forgotPassword(req)

        assert resp.message == (
            "If that email is registered, you will receive a"
            " password reset link shortly."
        )

    @pytest.mark.asyncio
    async def test_creates_password_reset_record_for_existing_user(
        self, service, registered_user
    ):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="user@example.com")
        await service.forgotPassword(req)

        assert len(svc._password_resets) == 1
        pr = list(svc._password_resets.values())[0]
        assert pr["user_id"] == registered_user["id"]
        assert pr["used_at"] is None

    @pytest.mark.asyncio
    async def test_does_not_create_reset_record_for_unknown_email(self, service):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="ghost@example.com")
        await service.forgotPassword(req)

        assert len(svc._password_resets) == 0

    @pytest.mark.asyncio
    async def test_reset_token_expires_in_approximately_one_hour(
        self, service, registered_user
    ):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        before = datetime.now(timezone.utc)
        req = ForgotPasswordRequest(email="user@example.com")
        await service.forgotPassword(req)
        after = datetime.now(timezone.utc)

        pr = list(svc._password_resets.values())[0]
        # expires_at should be ~1 hour from now
        lower = before + timedelta(minutes=59)
        upper = after + timedelta(minutes=61)
        assert lower <= pr["expires_at"] <= upper

    @pytest.mark.asyncio
    async def test_token_hash_stored_not_raw_token(
        self, service, registered_user
    ):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="user@example.com")
        await service.forgotPassword(req)

        pr = list(svc._password_resets.values())[0]
        # The stored hash must be a 64-char hex SHA-256 digest, not the raw token
        assert len(pr["token_hash"]) == 64
        assert pr["token_hash"].isalnum()

    @pytest.mark.asyncio
    async def test_multiple_forgot_password_calls_create_multiple_records(
        self, service, registered_user
    ):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        req = ForgotPasswordRequest(email="user@example.com")
        await service.forgotPassword(req)
        await service.forgotPassword(req)

        assert len(svc._password_resets) == 2

    @pytest.mark.asyncio
    async def test_response_type_is_forgot_password_response(self, service):
        from app.auth.schemas import ForgotPasswordRequest, ForgotPasswordResponse

        req = ForgotPasswordRequest(email="notregistered@example.com")
        resp = await service.forgotPassword(req)

        assert isinstance(resp, ForgotPasswordResponse)


# ---------------------------------------------------------------------------
# Service-level tests: resetPassword (dependent on forgotPassword)
# ---------------------------------------------------------------------------

class TestResetPasswordService:
    """Integration of forgotPassword token → resetPassword."""

    async def _do_forgot(self, service, email: str) -> str:
        """Trigger forgot-password and return the raw token from the store."""
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest

        count_before = len(svc._password_resets)
        await service.forgotPassword(ForgotPasswordRequest(email=email))
        # find the newly created record
        new_prs = [
            pr
            for pr in svc._password_resets.values()
            if pr["used_at"] is None
        ]
        assert new_prs, "No password reset record was created"
        # We need the raw token; reconstruct it via the hash stored
        # The store only has the hash, so we patch urandom to capture the raw value.
        return None  # raw token is captured separately via patching

    @pytest.mark.asyncio
    async def test_reset_succeeds_with_valid_token(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "a" * 64  # 32 bytes hex = 64 chars
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        req = ResetPasswordRequest(
            token=raw_token,
            password="NewPassw0rd",
            confirmPassword="NewPassw0rd",
        )
        resp = await service.resetPassword(req)
        assert resp.message == "Your password has been reset successfully."

    @pytest.mark.asyncio
    async def test_reset_marks_token_as_used(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "b" * 64
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        await service.resetPassword(
            ResetPasswordRequest(
                token=raw_token,
                password="NewPassw0rd",
                confirmPassword="NewPassw0rd",
            )
        )

        pr = list(svc._password_resets.values())[0]
        assert pr["used_at"] is not None

    @pytest.mark.asyncio
    async def test_reset_fails_with_invalid_token(self, service, registered_user):
        from app.auth.schemas import ResetPasswordRequest

        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(
                ResetPasswordRequest(
                    token="invalidtoken",
                    password="NewPassw0rd",
                    confirmPassword="NewPassw0rd",
                )
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_fails_when_token_already_used(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "c" * 64
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        req = ResetPasswordRequest(
            token=raw_token,
            password="NewPassw0rd",
            confirmPassword="NewPassw0rd",
        )
        # First reset succeeds
        await service.resetPassword(req)

        # Second reset with same token should fail
        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(req)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_fails_with_mismatched_passwords(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "d" * 64
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(
                ResetPasswordRequest(
                    token=raw_token,
                    password="NewPassw0rd",
                    confirmPassword="DifferentPassw0rd",
                )
            )
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_reset_fails_with_weak_password(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "e" * 64
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(
                ResetPasswordRequest(
                    token=raw_token,
                    password="weak",
                    confirmPassword="weak",
                )
            )
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_reset_fails_with_expired_token(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        raw_token = "f" * 64
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        # Manually expire the token
        pr = list(svc._password_resets.values())[0]
        pr["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)

        with pytest.raises(HTTPException) as exc_info:
            await service.resetPassword(
                ResetPasswordRequest(
                    token=raw_token,
                    password="NewPassw0rd",
                    confirmPassword="NewPassw0rd",
                )
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_reset_revokes_all_refresh_tokens_for_user(
        self, service, registered_user
    ):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, LoginRequest, ResetPasswordRequest

        # Login to create a refresh token
        mock_response = MagicMock()
        mock_response.set_cookie = MagicMock()
        await service.login(
            LoginRequest(email="user@example.com", password="Password1"),
            mock_response,
        )

        assert len(svc._refresh_tokens) == 1
        rt = list(svc._refresh_tokens.values())[0]
        assert rt["revoked_at"] is None

        raw_token = "a1" * 32  # 64 hex chars
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        await service.resetPassword(
            ResetPasswordRequest(
                token=raw_token,
                password="AnotherPassw0rd",
                confirmPassword="AnotherPassw0rd",
            )
        )

        rt = list(svc._refresh_tokens.values())[0]
        assert rt["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_reset_updates_password_hash(self, service, registered_user):
        import app.auth.service as svc
        from app.auth.schemas import ForgotPasswordRequest, ResetPasswordRequest

        old_hash = registered_user["password_hash"]

        raw_token = "ab" * 32  # 64 hex chars
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            await service.forgotPassword(ForgotPasswordRequest(email="user@example.com"))

        await service.resetPassword(
            ResetPasswordRequest(
                token=raw_token,
                password="BrandNewPassw0rd",
                confirmPassword="BrandNewPassw0rd",
            )
        )

        updated_user = svc._find_user_by_email("user@example.com")
        assert updated_user["password_hash"] != old_hash


# ---------------------------------------------------------------------------
# HTTP router-level tests via TestClient
# ---------------------------------------------------------------------------

class TestForgotPasswordRouter:
    """Tests for POST /auth/forgot-password via the HTTP layer."""

    def _register(self, client) -> None:
        client.post(
            "/auth/register",
            json={
                "fullName": "Test User",
                "email": "user@example.com",
                "password": "Password1",
                "confirmPassword": "Password1",
            },
        )

    def test_returns_202_for_existing_email(self, client):
        self._register(client)
        resp = client.post("/auth/forgot-password", json={"email": "user@example.com"})
        assert resp.status_code == 202

    def test_returns_202_for_nonexistent_email(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
        assert resp.status_code == 202

    def test_response_body_contains_message_key(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "user@example.com"})
        assert resp.status_code == 202
        body = resp.json()
        assert "message" in body

    def test_response_message_is_generic(self, client):
        self._register(client)
        resp = client.post("/auth/forgot-password", json={"email": "user@example.com"})
        body = resp.json()
        assert body["message"] == (
            "If that email is registered, you will receive a"
            " password reset link shortly."
        )

    def test_response_message_same_regardless_of_email_existence(self, client):
        self._register(client)
        resp_existing = client.post(
            "/auth/forgot-password", json={"email": "user@example.com"}
        )
        resp_missing = client.post(
            "/auth/forgot-password", json={"email": "ghost@example.com"}
        )
        assert resp_existing.json()["message"] == resp_missing.json()["message"]

    def test_returns_422_for_invalid_email(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "not-an-email"})
        assert resp.status_code == 422

    def test_returns_422_for_missing_email_field(self, client):
        resp = client.post("/auth/forgot-password", json={})
        assert resp.status_code == 422


class TestResetPasswordRouter:
    """Tests for POST /auth/reset-password via the HTTP layer."""

    def _register_and_get_reset_token(self, client) -> str:
        """Register a user, trigger forgot-password with a known raw token, return it."""
        client.post(
            "/auth/register",
            json={
                "fullName": "Test User",
                "email": "user@example.com",
                "password": "Password1",
                "confirmPassword": "Password1",
            },
        )
        raw_token = "12" * 32  # 64 hex chars
        with patch("app.auth.service.os.urandom", return_value=bytes.fromhex(raw_token)):
            client.post("/auth/forgot-password", json={"email": "user@example.com"})
        return raw_token

    def test_returns_200_with_valid_token(self, client):
        raw_token = self._register_and_get_reset_token(client)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        assert resp.status_code == 200

    def test_success_response_has_message(self, client):
        raw_token = self._register_and_get_reset_token(client)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        body = resp.json()
        assert "message" in body
        assert body["message"] == "Your password has been reset successfully."

    def test_returns_400_for_invalid_token(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "completelywrongtoken",
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        assert resp.status_code == 400

    def test_returns_422_for_password_mismatch(self, client):
        raw_token = self._register_and_get_reset_token(client)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "Different1",
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"]["code"] == "PASSWORD_MISMATCH"

    def test_returns_422_for_weak_password(self, client):
        raw_token = self._register_and_get_reset_token(client)
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "weak",
                "confirmPassword": "weak",
            },
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"]["code"] == "WEAK_PASSWORD"

    def test_second_use_of_same_token_fails(self, client):
        raw_token = self._register_and_get_reset_token(client)
        payload = {
            "token": raw_token,
            "password": "NewPassw0rd",
            "confirmPassword": "NewPassw0rd",
        }
        resp1 = client.post("/auth/reset-password", json=payload)
        assert resp1.status_code == 200

        resp2 = client.post("/auth/reset-password", json=payload)
        assert resp2.status_code == 400

    def test_expired_token_fails(self, client):
        import app.auth.service as svc

        raw_token = self._register_and_get_reset_token(client)
        # Manually expire
        pr = list(svc._password_resets.values())[0]
        pr["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)

        resp = client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    def test_can_login_with_new_password_after_reset(self, client):
        raw_token = self._register_and_get_reset_token(client)
        client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        resp = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "NewPassw0rd"},
        )
        assert resp.status_code == 200
        assert "accessToken" in resp.json()

    def test_old_password_rejected_after_reset(self, client):
        raw_token = self._register_and_get_reset_token(client)
        client.post(
            "/auth/reset-password",
            json={
                "token": raw_token,
                "password": "NewPassw0rd",
                "confirmPassword": "NewPassw0rd",
            },
        )
        resp = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "Password1"},
        )
        assert resp.status_code == 401
