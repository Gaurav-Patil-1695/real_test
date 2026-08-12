"""Unit tests for AuthService and helper functions in app.auth.service."""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# We need to reset the in-memory stores before every test so tests are
# independent.  We do that by monkey-patching the module-level dicts and
# counters directly.
# ---------------------------------------------------------------------------
import app.auth.service as svc
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.auth.service import (
    AuthService,
    _decode_access_token,
    _extract_bearer_token,
    _hash_password,
    _sha256,
    _validate_password_strength,
    _verify_password,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_stores():
    """Clear all in-memory stores and reset counters."""
    svc._users.clear()
    svc._password_resets.clear()
    svc._refresh_tokens.clear()
    svc._user_id_counter = 0
    svc._pr_id_counter = 0
    svc._rt_id_counter = 0


def _make_request(headers=None, cookies=None):
    """Return a minimal mock Request object."""
    req = MagicMock()
    req.headers = headers or {}
    req.cookies = cookies or {}
    return req


def _make_response():
    """Return a minimal mock Response object."""
    resp = MagicMock()
    return resp


@pytest.fixture(autouse=True)
def reset_stores():
    _reset_stores()
    yield
    _reset_stores()


# ===========================================================================
# Helper / utility function tests
# ===========================================================================

class TestSha256:
    def test_known_value(self):
        digest = _sha256("hello")
        assert digest == hashlib.sha256(b"hello").hexdigest()

    def test_empty_string(self):
        digest = _sha256("")
        assert digest == hashlib.sha256(b"").hexdigest()

    def test_deterministic(self):
        assert _sha256("abc") == _sha256("abc")

    def test_different_inputs_differ(self):
        assert _sha256("abc") != _sha256("xyz")


class TestHashAndVerifyPassword:
    def test_verify_correct_password(self):
        hashed = _hash_password("Secret1")
        assert _verify_password("Secret1", hashed) is True

    def test_verify_wrong_password(self):
        hashed = _hash_password("Secret1")
        assert _verify_password("wrong", hashed) is False

    def test_hash_is_not_plaintext(self):
        hashed = _hash_password("Secret1")
        assert hashed != "Secret1"


class TestValidatePasswordStrength:
    def test_too_short(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_password_strength("Ab1")
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail["error"]
        assert detail["code"] == "WEAK_PASSWORD"
        assert any("8 characters" in m for m in detail["details"])

    def test_no_uppercase(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_password_strength("abcdefg1")
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail["error"]
        assert any("uppercase" in m for m in detail["details"])

    def test_no_lowercase(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_password_strength("ABCDEFG1")
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail["error"]
        assert any("lowercase" in m for m in detail["details"])

    def test_no_digit(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_password_strength("Abcdefgh")
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail["error"]
        assert any("number" in m for m in detail["details"])

    def test_valid_password(self):
        # Should not raise
        _validate_password_strength("ValidPass1")

    def test_multiple_errors_accumulated(self):
        # Only 3 chars, no upper, no digit → multiple errors
        with pytest.raises(HTTPException) as exc_info:
            _validate_password_strength("abc")
        detail = exc_info.value.detail["error"]
        assert len(detail["details"]) > 1


class TestExtractBearerToken:
    def test_extracts_token(self):
        req = MagicMock()
        req.headers = {"Authorization": "Bearer mytoken123"}
        assert _extract_bearer_token(req) == "mytoken123"

    def test_missing_header_returns_none(self):
        req = MagicMock()
        req.headers = {}
        assert _extract_bearer_token(req) is None

    def test_non_bearer_returns_none(self):
        req = MagicMock()
        req.headers = {"Authorization": "Basic sometoken"}
        assert _extract_bearer_token(req) is None

    def test_bearer_prefix_case_sensitive(self):
        req = MagicMock()
        req.headers = {"Authorization": "bearer mytoken"}
        assert _extract_bearer_token(req) is None


class TestDecodeAccessToken:
    def _make_token(self, payload_overrides=None):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "1",
            "email": "test@example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        }
        if payload_overrides:
            payload.update(payload_overrides)
        return jwt.encode(payload, svc.SECRET_KEY, algorithm=svc.ALGORITHM)

    def test_valid_token(self):
        token = self._make_token()
        payload = _decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"

    def test_expired_token(self):
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": "1",
            "email": "test@example.com",
            "iat": int((now - timedelta(minutes=30)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }
        token = jwt.encode(expired_payload, svc.SECRET_KEY, algorithm=svc.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            _decode_access_token(token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "TOKEN_EXPIRED"

    def test_invalid_token(self):
        with pytest.raises(HTTPException) as exc_info:
            _decode_access_token("not.a.valid.token")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_TOKEN"

    def test_wrong_secret(self):
        token = jwt.encode({"sub": "1", "exp": 9999999999}, "wrong_secret", algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            _decode_access_token(token)
        assert exc_info.value.status_code == 401


# ===========================================================================
# AuthService tests
# ===========================================================================

class TestRegister:
    service = AuthService()

    @pytest.mark.asyncio
    async def test_successful_registration(self):
        body = RegisterRequest(
            fullName="John Doe",
            email="john@example.com",
            password="Password1",
            confirmPassword="Password1",
        )
        result = await self.service.register(body)
        assert result.id == 1
        assert result.full_name == "John Doe"
        assert result.email == "john@example.com"
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_password_mismatch(self):
        body = RegisterRequest(
            fullName="John Doe",
            email="john@example.com",
            password="Password1",
            confirmPassword="Different1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.register(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_weak_password(self):
        body = RegisterRequest(
            fullName="John Doe",
            email="john@example.com",
            password="weak",
            confirmPassword="weak",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.register(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_duplicate_email(self):
        body = RegisterRequest(
            fullName="John Doe",
            email="john@example.com",
            password="Password1",
            confirmPassword="Password1",
        )
        await self.service.register(body)
        with pytest.raises(HTTPException) as exc_info:
            await self.service.register(body)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"]["code"] == "EMAIL_TAKEN"

    @pytest.mark.asyncio
    async def test_user_stored_in_memory(self):
        body = RegisterRequest(
            fullName="Jane Doe",
            email="jane@example.com",
            password="Password1",
            confirmPassword="Password1",
        )
        result = await self.service.register(body)
        assert result.id in svc._users
        stored = svc._users[result.id]
        assert stored["email"] == "jane@example.com"
        assert stored["is_active"] is True

    @pytest.mark.asyncio
    async def test_increments_id(self):
        body1 = RegisterRequest(
            fullName="A", email="a@example.com", password="Password1", confirmPassword="Password1"
        )
        body2 = RegisterRequest(
            fullName="B", email="b@example.com", password="Password1", confirmPassword="Password1"
        )
        r1 = await self.service.register(body1)
        r2 = await self.service.register(body2)
        assert r2.id == r1.id + 1


class TestLogin:
    service = AuthService()

    async def _register_user(self, email="user@example.com", password="Password1"):
        body = RegisterRequest(
            fullName="Test User",
            email=email,
            password=password,
            confirmPassword=password,
        )
        return await self.service.register(body)

    @pytest.mark.asyncio
    async def test_successful_login(self):
        await self._register_user()
        body = LoginRequest(email="user@example.com", password="Password1")
        response = _make_response()
        result = await self.service.login(body, response)
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user.email == "user@example.com"
        response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_email(self):
        body = LoginRequest(email="notexist@example.com", password="Password1")
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.login(body, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_wrong_password(self):
        await self._register_user()
        body = LoginRequest(email="user@example.com", password="WrongPass1")
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.login(body, response)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_inactive_user(self):
        await self._register_user()
        # Manually deactivate user
        for user in svc._users.values():
            if user["email"] == "user@example.com":
                user["is_active"] = False
        body = LoginRequest(email="user@example.com", password="Password1")
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.login(body, response)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.asyncio
    async def test_remember_me_sets_longer_cookie(self):
        await self._register_user()
        body = LoginRequest(email="user@example.com", password="Password1", rememberMe=True)
        response = _make_response()
        await self.service.login(body, response)
        call_kwargs = response.set_cookie.call_args[1]
        expected_max_age = svc.REFRESH_TOKEN_REMEMBER_DAYS * 86400
        assert call_kwargs["max_age"] == expected_max_age

    @pytest.mark.asyncio
    async def test_no_remember_me_sets_shorter_cookie(self):
        await self._register_user()
        body = LoginRequest(email="user@example.com", password="Password1", rememberMe=False)
        response = _make_response()
        await self.service.login(body, response)
        call_kwargs = response.set_cookie.call_args[1]
        expected_max_age = svc.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        assert call_kwargs["max_age"] == expected_max_age

    @pytest.mark.asyncio
    async def test_refresh_token_stored(self):
        await self._register_user()
        body = LoginRequest(email="user@example.com", password="Password1")
        response = _make_response()
        await self.service.login(body, response)
        assert len(svc._refresh_tokens) == 1

    @pytest.mark.asyncio
    async def test_access_token_is_valid_jwt(self):
        reg = await self._register_user()
        body = LoginRequest(email="user@example.com", password="Password1")
        response = _make_response()
        result = await self.service.login(body, response)
        payload = jwt.decode(result.access_token, svc.SECRET_KEY, algorithms=[svc.ALGORITHM])
        assert payload["sub"] == str(reg.id)
        assert payload["email"] == "user@example.com"


class TestForgotPassword:
    service = AuthService()

    async def _register_user(self, email="user@example.com"):
        body = RegisterRequest(
            fullName="Test User",
            email=email,
            password="Password1",
            confirmPassword="Password1",
        )
        return await self.service.register(body)

    @pytest.mark.asyncio
    async def test_known_email_creates_reset_record(self):
        await self._register_user()
        body = ForgotPasswordRequest(email="user@example.com")
        result = await self.service.forgotPassword(body)
        assert "password reset link" in result.message
        assert len(svc._password_resets) == 1

    @pytest.mark.asyncio
    async def test_unknown_email_returns_same_message(self):
        body = ForgotPasswordRequest(email="unknown@example.com")
        result = await self.service.forgotPassword(body)
        assert "password reset link" in result.message
        assert len(svc._password_resets) == 0

    @pytest.mark.asyncio
    async def test_reset_record_expires_in_one_hour(self):
        await self._register_user()
        body = ForgotPasswordRequest(email="user@example.com")
        await self.service.forgotPassword(body)
        pr = list(svc._password_resets.values())[0]
        delta = pr["expires_at"] - pr["created_at"]
        assert abs(delta.total_seconds() - 3600) < 5


class TestResetPassword:
    service = AuthService()

    async def _setup_user_and_reset_token(self, email="user@example.com", password="Password1"):
        reg_body = RegisterRequest(
            fullName="Test User",
            email=email,
            password=password,
            confirmPassword=password,
        )
        await self.service.register(reg_body)
        raw_token = os.urandom(32).hex()
        token_hash = _sha256(raw_token)
        now = datetime.now(timezone.utc)
        pr_id = svc._next_pr_id()
        user = svc._find_user_by_email(email)
        svc._password_resets[pr_id] = {
            "id": pr_id,
            "user_id": user["id"],
            "token_hash": token_hash,
            "expires_at": now + timedelta(hours=1),
            "used_at": None,
            "created_at": now,
        }
        return raw_token

    @pytest.mark.asyncio
    async def test_successful_reset(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        result = await self.service.resetPassword(body)
        assert "reset successfully" in result.message

    @pytest.mark.asyncio
    async def test_password_updated_in_store(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        await self.service.resetPassword(body)
        user = svc._find_user_by_email("user@example.com")
        assert _verify_password("NewPassword1", user["password_hash"])

    @pytest.mark.asyncio
    async def test_token_marked_as_used(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        await self.service.resetPassword(body)
        pr = list(svc._password_resets.values())[0]
        assert pr["used_at"] is not None

    @pytest.mark.asyncio
    async def test_passwords_mismatch(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="Different1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token="invalid_token_value",
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.resetPassword(body)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.asyncio
    async def test_expired_token(self):
        raw_token = await self._setup_user_and_reset_token()
        # Manually expire the token
        pr = list(svc._password_resets.values())[0]
        pr["expires_at"] = datetime.now(timezone.utc) - timedelta(hours=1)
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.resetPassword(body)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_already_used_token(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        await self.service.resetPassword(body)
        # Try again
        body2 = ResetPasswordRequest(
            token=raw_token,
            password="AnotherPass1",
            confirmPassword="AnotherPass1",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.resetPassword(body2)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_refresh_tokens_revoked_on_reset(self):
        raw_token = await self._setup_user_and_reset_token()
        # Simulate a live refresh token for this user
        user = svc._find_user_by_email("user@example.com")
        now = datetime.now(timezone.utc)
        rt_id = svc._next_rt_id()
        svc._refresh_tokens[rt_id] = {
            "id": rt_id,
            "user_id": user["id"],
            "token_hash": _sha256("sometoken"),
            "expires_at": now + timedelta(days=7),
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPassword1",
            confirmPassword="NewPassword1",
        )
        await self.service.resetPassword(body)
        rt = svc._refresh_tokens[rt_id]
        assert rt["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_weak_new_password(self):
        raw_token = await self._setup_user_and_reset_token()
        body = ResetPasswordRequest(
            token=raw_token,
            password="weak",
            confirmPassword="weak",
        )
        with pytest.raises(HTTPException) as exc_info:
            await self.service.resetPassword(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"


class TestMe:
    service = AuthService()

    async def _register_and_get_token(self, email="user@example.com"):
        reg_body = RegisterRequest(
            fullName="Test User",
            email=email,
            password="Password1",
            confirmPassword="Password1",
        )
        reg = await self.service.register(reg_body)
        login_body = LoginRequest(email=email, password="Password1")
        response = _make_response()
        login_result = await self.service.login(login_body, response)
        return login_result.access_token, reg

    @pytest.mark.asyncio
    async def test_me_with_valid_token(self):
        token, reg = await self._register_and_get_token()
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        result = await self.service.me(request)
        assert result.id == reg.id
        assert result.email == "user@example.com"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_me_missing_token(self):
        request = _make_request(headers={})
        with pytest.raises(HTTPException) as exc_info:
            await self.service.me(request)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_me_invalid_token(self):
        request = _make_request(headers={"Authorization": "Bearer badtoken"})
        with pytest.raises(HTTPException) as exc_info:
            await self.service.me(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_me_user_not_found(self):
        # Create a valid token for a user_id that doesn't exist in store
        from app.auth.service import _create_access_token
        token = _create_access_token(9999, "ghost@example.com")
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        with pytest.raises(HTTPException) as exc_info:
            await self.service.me(request)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "USER_NOT_FOUND"


class TestLogout:
    service = AuthService()

    async def _setup_logged_in_user(self, email="user@example.com"):
        reg_body = RegisterRequest(
            fullName="Test User",
            email=email,
            password="Password1",
            confirmPassword="Password1",
        )
        await self.service.register(reg_body)
        login_body = LoginRequest(email=email, password="Password1")
        response = _make_response()
        login_result = await self.service.login(login_body, response)
        return login_result.access_token

    @pytest.mark.asyncio
    async def test_logout_with_valid_token(self):
        token = await self._setup_logged_in_user()
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        response = _make_response()
        result = await self.service.logout(request, response)
        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_revokes_refresh_tokens(self):
        token = await self._setup_logged_in_user()
        # Confirm refresh token exists
        assert any(rt["revoked_at"] is None for rt in svc._refresh_tokens.values())
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        response = _make_response()
        await self.service.logout(request, response)
        assert all(rt["revoked_at"] is not None for rt in svc._refresh_tokens.values())

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self):
        token = await self._setup_logged_in_user()
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        response = _make_response()
        await self.service.logout(request, response)
        response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_without_token_still_clears_cookie(self):
        request = _make_request(headers={})
        response = _make_response()
        result = await self.service.logout(request, response)
        assert result.message == "Logged out successfully."
        response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_still_clears_cookie(self):
        request = _make_request(headers={"Authorization": "Bearer badtoken"})
        response = _make_response()
        result = await self.service.logout(request, response)
        assert result.message == "Logged out successfully."
        response.delete_cookie.assert_called_once()


class TestRefresh:
    service = AuthService()

    async def _setup_and_get_refresh_token(self, email="user@example.com", remember_me=False):
        reg_body = RegisterRequest(
            fullName="Test User",
            email=email,
            password="Password1",
            confirmPassword="Password1",
        )
        await self.service.register(reg_body)
        login_body = LoginRequest(email=email, password="Password1", rememberMe=remember_me)
        # Capture the raw refresh token from set_cookie call
        response = _make_response()
        await self.service.login(login_body, response)
        # The raw refresh_token was passed as value arg
        call_kwargs = response.set_cookie.call_args[1]
        raw_token = call_kwargs["value"]
        return raw_token

    @pytest.mark.asyncio
    async def test_successful_refresh(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response = _make_response()
        result = await self.service.refresh(request, response, raw_token)
        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_rotates_token(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response = _make_response()
        await self.service.refresh(request, response, raw_token)
        # Old token should be revoked
        old_hash = _sha256(raw_token)
        old_rt = None
        for rt in svc._refresh_tokens.values():
            if rt["token_hash"] == old_hash:
                old_rt = rt
                break
        assert old_rt is not None
        assert old_rt["revoked_at"] is not None
        # A new token should exist
        assert any(rt["revoked_at"] is None for rt in svc._refresh_tokens.values())

    @pytest.mark.asyncio
    async def test_refresh_missing_token(self):
        request = _make_request()
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.refresh(request, response, None)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "MISSING_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self):
        request = _make_request()
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.refresh(request, response, "not_a_valid_token")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.asyncio
    async def test_refresh_reuse_detection(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response1 = _make_response()
        # First refresh — OK
        await self.service.refresh(request, response1, raw_token)
        # Second use of the SAME (now revoked) token — reuse detected
        response2 = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.refresh(request, response2, raw_token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_REUSE"

    @pytest.mark.asyncio
    async def test_refresh_reuse_revokes_all_user_tokens(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response1 = _make_response()
        await self.service.refresh(request, response1, raw_token)
        response2 = _make_response()
        with pytest.raises(HTTPException):
            await self.service.refresh(request, response2, raw_token)
        # All tokens for this user should be revoked
        assert all(rt["revoked_at"] is not None for rt in svc._refresh_tokens.values())

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self):
        raw_token = await self._setup_and_get_refresh_token()
        # Manually expire the refresh token
        token_hash = _sha256(raw_token)
        for rt in svc._refresh_tokens.values():
            if rt["token_hash"] == token_hash:
                rt["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
        request = _make_request()
        response = _make_response()
        with pytest.raises(HTTPException) as exc_info:
            await self.service.refresh(request, response, raw_token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"]["code"] == "REFRESH_TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_refresh_sets_new_cookie(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response = _make_response()
        await self.service.refresh(request, response, raw_token)
        response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_remember_me_preserves_flag(self):
        raw_token = await self._setup_and_get_refresh_token(remember_me=True)
        request = _make_request()
        response = _make_response()
        await self.service.refresh(request, response, raw_token)
        call_kwargs = response.set_cookie.call_args[1]
        expected_max_age = svc.REFRESH_TOKEN_REMEMBER_DAYS * 86400
        assert call_kwargs["max_age"] == expected_max_age

    @pytest.mark.asyncio
    async def test_refresh_new_access_token_is_valid(self):
        raw_token = await self._setup_and_get_refresh_token()
        request = _make_request()
        response = _make_response()
        result = await self.service.refresh(request, response, raw_token)
        payload = jwt.decode(result.access_token, svc.SECRET_KEY, algorithms=[svc.ALGORITHM])
        assert "sub" in payload
        assert "email" in payload


# ===========================================================================
# Router integration tests (via TestClient)
# ===========================================================================

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_stores_router():
    _reset_stores()
    yield
    _reset_stores()


class TestRouterRegister:
    def test_register_success(self):
        resp = client.post("/auth/register", json={
            "fullName": "Alice",
            "email": "alice@example.com",
            "password": "Password1",
            "confirmPassword": "Password1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert data["fullName"] == "Alice"
        assert "id" in data
        assert "createdAt" in data

    def test_register_password_mismatch(self):
        resp = client.post("/auth/register", json={
            "fullName": "Alice",
            "email": "alice@example.com",
            "password": "Password1",
            "confirmPassword": "Different1",
        })
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "PASSWORD_MISMATCH"

    def test_register_duplicate_email(self):
        payload = {
            "fullName": "Alice",
            "email": "alice@example.com",
            "password": "Password1",
            "confirmPassword": "Password1",
        }
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409
        assert resp.json()["detail"]["error"]["code"] == "EMAIL_TAKEN"


class TestRouterLogin:
    def _register(self, email="user@example.com"):
        client.post("/auth/register", json={
            "fullName": "Test",
            "email": email,
            "password": "Password1",
            "confirmPassword": "Password1",
        })

    def test_login_success(self):
        self._register()
        resp = client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "Password1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "accessToken" in data
        assert data["tokenType"] == "bearer"
        assert "user" in data

    def test_login_bad_credentials(self):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "Password1",
        })
        assert resp.status_code == 401


class TestRouterForgotPassword:
    def test_forgot_password_always_202(self):
        resp = client.post("/auth/forgot-password", json={"email": "any@example.com"})
        assert resp.status_code == 202
        assert "message" in resp.json()


class TestRouterMe:
    def _get_access_token(self, email="user@example.com"):
        client.post("/auth/register", json={
            "fullName": "Test",
            "email": email,
            "password": "Password1",
            "confirmPassword": "Password1",
        })
        resp = client.post("/auth/login", json={"email": email, "password": "Password1"})
        return resp.json()["accessToken"]

    def test_me_success(self):
        token = self._get_access_token()
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@example.com"

    def test_me_missing_token(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


class TestRouterLogout:
    def test_logout_success(self):
        client.post("/auth/register", json={
            "fullName": "Test",
            "email": "user@example.com",
            "password": "Password1",
            "confirmPassword": "Password1",
        })
        login_resp = client.post("/auth/login", json={"email": "user@example.com", "password": "Password1"})
        token = login_resp.json()["accessToken"]
        resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully."


class TestRouterRefresh:
    def test_refresh_missing_cookie_returns_401(self):
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401
        assert resp.json()["detail"]["error"]["code"] == "MISSING_REFRESH_TOKEN"

    def test_refresh_invalid_cookie_returns_401(self):
        resp = client.post("/auth/refresh", cookies={"refresh_token": "bad_value"})
        assert resp.status_code == 401

    def test_refresh_success_with_valid_cookie(self):
        client.post("/auth/register", json={
            "fullName": "Test",
            "email": "user@example.com",
            "password": "Password1",
            "confirmPassword": "Password1",
        })
        login_resp = client.post("/auth/login", json={"email": "user@example.com", "password": "Password1"})
        # Extract the refresh_token cookie from login response
        rt_cookie = login_resp.cookies.get("refresh_token")
        assert rt_cookie is not None
        resp = client.post("/auth/refresh", cookies={"refresh_token": rt_cookie})
        assert resp.status_code == 200
        data = resp.json()
        assert "accessToken" in data
        assert data["tokenType"] == "bearer"


class TestRouterResetPassword:
    def _setup_reset_token(self, email="user@example.com"):
        client.post("/auth/register", json={
            "fullName": "Test",
            "email": email,
            "password": "Password1",
            "confirmPassword": "Password1",
        })
        client.post("/auth/forgot-password", json={"email": email})
        # Pull the raw token from in-memory store
        pr = list(svc._password_resets.values())[0]
        # We need the raw token — store the hash, so reconstruct by replacing with known raw
        raw_token = os.urandom(32).hex()
        pr["token_hash"] = _sha256(raw_token)
        return raw_token

    def test_reset_password_success(self):
        raw_token = self._setup_reset_token()
        resp = client.post("/auth/reset-password", json={
            "token": raw_token,
            "password": "NewPassword1",
            "confirmPassword": "NewPassword1",
        })
        assert resp.status_code == 200
        assert "reset successfully" in resp.json()["message"]

    def test_reset_password_invalid_token(self):
        resp = client.post("/auth/reset-password", json={
            "token": "badtoken",
            "password": "NewPassword1",
            "confirmPassword": "NewPassword1",
        })
        assert resp.status_code == 400
