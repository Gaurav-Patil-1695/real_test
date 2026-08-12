"""Unit tests for app.auth.service and app.auth.router (via TestClient)."""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, Response
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers to reach into the in-memory stores the service uses
# ---------------------------------------------------------------------------
import app.auth.service as svc_module
from app.auth.service import (
    AuthService,
    ALGORITHM,
    SECRET_KEY,
    _sha256,
    _hash_password,
    _verify_password,
    _create_access_token,
    _validate_password_strength,
)
from app.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_stores():
    """Reset all in-memory stores and counters before every test."""
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


@pytest.fixture()
def service():
    return AuthService()


@pytest.fixture()
def mock_response():
    resp = MagicMock(spec=Response)
    return resp


@pytest.fixture()
def mock_request_factory():
    """Return a callable that produces a mock Request with the given Bearer token."""
    def _make(token: str | None = None):
        req = MagicMock()
        if token:
            req.headers = {"Authorization": f"Bearer {token}"}
        else:
            req.headers = {}
        return req
    return _make


VALID_PASSWORD = "Passw0rd!"
VALID_EMAIL = "user@example.com"
VALID_FULL_NAME = "Test User"


def make_register_body(
    email=VALID_EMAIL,
    password=VALID_PASSWORD,
    confirm_password=VALID_PASSWORD,
    full_name=VALID_FULL_NAME,
):
    return RegisterRequest(
        fullName=full_name,
        email=email,
        password=password,
        confirmPassword=confirm_password,
    )


def make_login_body(email=VALID_EMAIL, password=VALID_PASSWORD, remember_me=None):
    return LoginRequest(email=email, password=password, rememberMe=remember_me)


# ---------------------------------------------------------------------------
# Helper utilities (pure functions)
# ---------------------------------------------------------------------------

class TestSha256:
    def test_deterministic(self):
        assert _sha256("hello") == _sha256("hello")

    def test_known_value(self):
        expected = hashlib.sha256(b"hello").hexdigest()
        assert _sha256("hello") == expected

    def test_different_inputs_differ(self):
        assert _sha256("a") != _sha256("b")


class TestHashPassword:
    def test_round_trip(self):
        hashed = _hash_password("MySecret1")
        assert _verify_password("MySecret1", hashed)

    def test_wrong_password_fails(self):
        hashed = _hash_password("MySecret1")
        assert not _verify_password("wrongpass", hashed)


class TestValidatePasswordStrength:
    def test_valid_password_passes(self):
        _validate_password_strength("Passw0rd")

    def test_too_short_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_password_strength("Ab1")
        assert exc.value.status_code == 422
        assert "WEAK_PASSWORD" in str(exc.value.detail)

    def test_no_uppercase_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_password_strength("passw0rd")
        assert exc.value.status_code == 422

    def test_no_lowercase_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_password_strength("PASSW0RD")
        assert exc.value.status_code == 422

    def test_no_digit_raises(self):
        with pytest.raises(HTTPException) as exc:
            _validate_password_strength("Password")
        assert exc.value.status_code == 422

    def test_error_detail_structure(self):
        with pytest.raises(HTTPException) as exc:
            _validate_password_strength("short")
        detail = exc.value.detail
        assert "error" in detail
        assert detail["error"]["code"] == "WEAK_PASSWORD"
        assert isinstance(detail["error"]["details"], list)


class TestCreateAccessToken:
    def test_decodes_correctly(self):
        token = _create_access_token(1, "a@b.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "1"
        assert payload["email"] == "a@b.com"

    def test_has_exp(self):
        token = _create_access_token(1, "a@b.com")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload


# ---------------------------------------------------------------------------
# AuthService.register
# ---------------------------------------------------------------------------

class TestRegister:
    @pytest.mark.anyio
    async def test_register_success(self, service):
        body = make_register_body()
        result = await service.register(body)
        assert result.email == VALID_EMAIL
        assert result.fullName == VALID_FULL_NAME
        assert result.id == 1

    @pytest.mark.anyio
    async def test_register_stores_user(self, service):
        body = make_register_body()
        await service.register(body)
        assert len(svc_module._users) == 1

    @pytest.mark.anyio
    async def test_register_password_mismatch_raises(self, service):
        body = make_register_body(confirm_password="DifferentPass1")
        with pytest.raises(HTTPException) as exc:
            await service.register(body)
        assert exc.value.status_code == 422
        assert exc.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.anyio
    async def test_register_weak_password_raises(self, service):
        body = make_register_body(password="weak", confirm_password="weak")
        with pytest.raises(HTTPException) as exc:
            await service.register(body)
        assert exc.value.status_code == 422
        assert exc.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.anyio
    async def test_register_duplicate_email_raises(self, service):
        body = make_register_body()
        await service.register(body)
        with pytest.raises(HTTPException) as exc:
            await service.register(body)
        assert exc.value.status_code == 409
        assert exc.value.detail["error"]["code"] == "EMAIL_TAKEN"

    @pytest.mark.anyio
    async def test_register_increments_id(self, service):
        r1 = await service.register(make_register_body(email="a@b.com"))
        r2 = await service.register(make_register_body(email="b@b.com"))
        assert r2.id == r1.id + 1

    @pytest.mark.anyio
    async def test_register_response_has_created_at(self, service):
        result = await service.register(make_register_body())
        # createdAt should be a parseable ISO timestamp
        assert "T" in result.createdAt


# ---------------------------------------------------------------------------
# AuthService.login
# ---------------------------------------------------------------------------

class TestLogin:
    @pytest.mark.anyio
    async def test_login_success(self, service, mock_response):
        await service.register(make_register_body())
        result = await service.login(make_login_body(), mock_response)
        assert result.tokenType == "bearer"
        assert result.accessToken
        assert result.user.email == VALID_EMAIL

    @pytest.mark.anyio
    async def test_login_sets_cookie(self, service, mock_response):
        await service.register(make_register_body())
        await service.login(make_login_body(), mock_response)
        mock_response.set_cookie.assert_called_once()

    @pytest.mark.anyio
    async def test_login_wrong_email_raises(self, service, mock_response):
        with pytest.raises(HTTPException) as exc:
            await service.login(make_login_body(email="no@one.com"), mock_response)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_wrong_password_raises(self, service, mock_response):
        await service.register(make_register_body())
        with pytest.raises(HTTPException) as exc:
            await service.login(make_login_body(password="WrongPass1"), mock_response)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.anyio
    async def test_login_inactive_user_raises(self, service, mock_response):
        await service.register(make_register_body())
        # Mark user inactive
        for u in svc_module._users.values():
            u["is_active"] = False
        with pytest.raises(HTTPException) as exc:
            await service.login(make_login_body(), mock_response)
        assert exc.value.status_code == 403
        assert exc.value.detail["error"]["code"] == "ACCOUNT_INACTIVE"

    @pytest.mark.anyio
    async def test_login_remember_me_true_uses_longer_expiry(self, service, mock_response):
        await service.register(make_register_body())
        await service.login(make_login_body(remember_me=True), mock_response)
        call_kwargs = mock_response.set_cookie.call_args
        max_age = call_kwargs.kwargs.get("max_age") or call_kwargs[1].get("max_age")
        assert max_age == svc_module.REFRESH_TOKEN_REMEMBER_DAYS * 86400

    @pytest.mark.anyio
    async def test_login_remember_me_false_uses_shorter_expiry(self, service, mock_response):
        await service.register(make_register_body())
        await service.login(make_login_body(remember_me=False), mock_response)
        call_kwargs = mock_response.set_cookie.call_args
        max_age = call_kwargs.kwargs.get("max_age") or call_kwargs[1].get("max_age")
        assert max_age == svc_module.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    @pytest.mark.anyio
    async def test_login_stores_refresh_token(self, service, mock_response):
        await service.register(make_register_body())
        await service.login(make_login_body(), mock_response)
        assert len(svc_module._refresh_tokens) == 1

    @pytest.mark.anyio
    async def test_login_access_token_is_valid_jwt(self, service, mock_response):
        await service.register(make_register_body())
        result = await service.login(make_login_body(), mock_response)
        payload = jwt.decode(result.accessToken, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == VALID_EMAIL


# ---------------------------------------------------------------------------
# AuthService.forgotPassword
# ---------------------------------------------------------------------------

class TestForgotPassword:
    @pytest.mark.anyio
    async def test_returns_generic_message_for_registered_email(self, service):
        await service.register(make_register_body())
        result = await service.forgotPassword(ForgotPasswordRequest(email=VALID_EMAIL))
        assert "password reset link" in result.message

    @pytest.mark.anyio
    async def test_returns_generic_message_for_unknown_email(self, service):
        result = await service.forgotPassword(ForgotPasswordRequest(email="nobody@x.com"))
        assert "password reset link" in result.message

    @pytest.mark.anyio
    async def test_stores_reset_record_for_known_email(self, service):
        await service.register(make_register_body())
        await service.forgotPassword(ForgotPasswordRequest(email=VALID_EMAIL))
        assert len(svc_module._password_resets) == 1

    @pytest.mark.anyio
    async def test_does_not_store_reset_record_for_unknown_email(self, service):
        await service.forgotPassword(ForgotPasswordRequest(email="nobody@x.com"))
        assert len(svc_module._password_resets) == 0


# ---------------------------------------------------------------------------
# AuthService.resetPassword
# ---------------------------------------------------------------------------

class TestResetPassword:
    async def _setup_reset(self, service):
        """Register a user and manually insert a password reset record."""
        await service.register(make_register_body())
        raw_token = "abcdef1234567890" * 4  # 64 chars
        token_hash = _sha256(raw_token)
        now = datetime.now(timezone.utc)
        pr_id = svc_module._next_pr_id()
        user_id = list(svc_module._users.keys())[0]
        svc_module._password_resets[pr_id] = {
            "id": pr_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": now + timedelta(hours=1),
            "used_at": None,
            "created_at": now,
        }
        return raw_token, user_id

    @pytest.mark.anyio
    async def test_reset_success(self, service):
        raw_token, _ = await self._setup_reset(service)
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        result = await service.resetPassword(body)
        assert "successfully" in result.message

    @pytest.mark.anyio
    async def test_reset_marks_record_as_used(self, service):
        raw_token, _ = await self._setup_reset(service)
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        await service.resetPassword(body)
        pr = list(svc_module._password_resets.values())[0]
        assert pr["used_at"] is not None

    @pytest.mark.anyio
    async def test_reset_updates_password(self, service, mock_response):
        raw_token, _ = await self._setup_reset(service)
        new_pass = "NewPass1!"
        body = ResetPasswordRequest(
            token=raw_token,
            password=new_pass,
            confirmPassword=new_pass,
        )
        await service.resetPassword(body)
        # Login with new password should succeed
        result = await service.login(make_login_body(password=new_pass), mock_response)
        assert result.accessToken

    @pytest.mark.anyio
    async def test_reset_revokes_existing_refresh_tokens(self, service, mock_response):
        raw_token, user_id = await self._setup_reset(service)
        # Give the user a refresh token
        now = datetime.now(timezone.utc)
        rt_id = svc_module._next_rt_id()
        svc_module._refresh_tokens[rt_id] = {
            "id": rt_id,
            "user_id": user_id,
            "token_hash": _sha256("some_refresh_token"),
            "expires_at": now + timedelta(days=7),
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        await service.resetPassword(body)
        for rt in svc_module._refresh_tokens.values():
            assert rt["revoked_at"] is not None

    @pytest.mark.anyio
    async def test_reset_invalid_token_raises(self, service):
        body = ResetPasswordRequest(
            token="nonexistent_token",
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        with pytest.raises(HTTPException) as exc:
            await service.resetPassword(body)
        assert exc.value.status_code == 400
        assert exc.value.detail["error"]["code"] == "INVALID_OR_EXPIRED_TOKEN"

    @pytest.mark.anyio
    async def test_reset_password_mismatch_raises(self, service):
        body = ResetPasswordRequest(
            token="any_token",
            password="NewPass1!",
            confirmPassword="Different1!",
        )
        with pytest.raises(HTTPException) as exc:
            await service.resetPassword(body)
        assert exc.value.status_code == 422
        assert exc.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.anyio
    async def test_reset_expired_token_raises(self, service):
        await service.register(make_register_body())
        raw_token = "expiredtoken" * 5
        token_hash = _sha256(raw_token)
        now = datetime.now(timezone.utc)
        pr_id = svc_module._next_pr_id()
        user_id = list(svc_module._users.keys())[0]
        svc_module._password_resets[pr_id] = {
            "id": pr_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": now - timedelta(hours=1),  # already expired
            "used_at": None,
            "created_at": now - timedelta(hours=2),
        }
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        with pytest.raises(HTTPException) as exc:
            await service.resetPassword(body)
        assert exc.value.status_code == 400

    @pytest.mark.anyio
    async def test_reset_already_used_token_raises(self, service):
        await service.register(make_register_body())
        raw_token = "usedtoken" * 8
        token_hash = _sha256(raw_token)
        now = datetime.now(timezone.utc)
        pr_id = svc_module._next_pr_id()
        user_id = list(svc_module._users.keys())[0]
        svc_module._password_resets[pr_id] = {
            "id": pr_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": now + timedelta(hours=1),
            "used_at": now - timedelta(minutes=5),  # already used
            "created_at": now - timedelta(hours=1),
        }
        body = ResetPasswordRequest(
            token=raw_token,
            password="NewPass1!",
            confirmPassword="NewPass1!",
        )
        with pytest.raises(HTTPException) as exc:
            await service.resetPassword(body)
        assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# AuthService.me
# ---------------------------------------------------------------------------

class TestMe:
    @pytest.mark.anyio
    async def test_me_success(self, service, mock_request_factory):
        await service.register(make_register_body())
        token = _create_access_token(1, VALID_EMAIL)
        request = mock_request_factory(token)
        result = await service.me(request)
        assert result.email == VALID_EMAIL
        assert result.id == 1

    @pytest.mark.anyio
    async def test_me_no_token_raises(self, service, mock_request_factory):
        request = mock_request_factory(None)
        with pytest.raises(HTTPException) as exc:
            await service.me(request)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "MISSING_TOKEN"

    @pytest.mark.anyio
    async def test_me_invalid_token_raises(self, service, mock_request_factory):
        request = mock_request_factory("thisis.invalid.token")
        with pytest.raises(HTTPException) as exc:
            await service.me(request)
        assert exc.value.status_code == 401

    @pytest.mark.anyio
    async def test_me_expired_token_raises(self, service, mock_request_factory):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "1",
            "email": VALID_EMAIL,
            "iat": int((now - timedelta(hours=1)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        request = mock_request_factory(expired_token)
        with pytest.raises(HTTPException) as exc:
            await service.me(request)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "TOKEN_EXPIRED"

    @pytest.mark.anyio
    async def test_me_user_not_found_raises(self, service, mock_request_factory):
        # Token for non-existent user
        token = _create_access_token(999, VALID_EMAIL)
        request = mock_request_factory(token)
        with pytest.raises(HTTPException) as exc:
            await service.me(request)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "USER_NOT_FOUND"


# ---------------------------------------------------------------------------
# AuthService.logout
# ---------------------------------------------------------------------------

class TestLogout:
    @pytest.mark.anyio
    async def test_logout_success_returns_message(self, service, mock_request_factory, mock_response):
        request = mock_request_factory(None)
        result = await service.logout(request, mock_response)
        assert "Logged out" in result.message

    @pytest.mark.anyio
    async def test_logout_clears_cookie(self, service, mock_request_factory, mock_response):
        request = mock_request_factory(None)
        await service.logout(request, mock_response)
        mock_response.delete_cookie.assert_called_once()

    @pytest.mark.anyio
    async def test_logout_revokes_refresh_tokens_for_user(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        token = _create_access_token(1, VALID_EMAIL)
        # Manually insert refresh token
        now = datetime.now(timezone.utc)
        svc_module._refresh_tokens[1] = {
            "id": 1,
            "user_id": 1,
            "token_hash": _sha256("sometoken"),
            "expires_at": now + timedelta(days=7),
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }
        request = mock_request_factory(token)
        await service.logout(request, mock_response)
        assert svc_module._refresh_tokens[1]["revoked_at"] is not None

    @pytest.mark.anyio
    async def test_logout_with_invalid_token_still_succeeds(self, service, mock_request_factory, mock_response):
        request = mock_request_factory("bad.token.value")
        # Should not raise
        result = await service.logout(request, mock_response)
        assert result.message


# ---------------------------------------------------------------------------
# AuthService.refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def _insert_refresh_token(self, user_id, raw_token, remember_me=False, days_until_expiry=7, revoked=False):
        now = datetime.now(timezone.utc)
        rt_id = svc_module._next_rt_id()
        svc_module._refresh_tokens[rt_id] = {
            "id": rt_id,
            "user_id": user_id,
            "token_hash": _sha256(raw_token),
            "expires_at": now + timedelta(days=days_until_expiry),
            "revoked_at": now - timedelta(seconds=1) if revoked else None,
            "remember_me": remember_me,
            "created_at": now,
        }
        return rt_id

    @pytest.mark.anyio
    async def test_refresh_success_returns_new_access_token(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        raw_token = "valid_refresh_token"
        self._insert_refresh_token(1, raw_token)
        request = mock_request_factory()
        result = await service.refresh(request, mock_response, raw_token)
        assert result.accessToken
        assert result.tokenType == "bearer"

    @pytest.mark.anyio
    async def test_refresh_rotates_token(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        raw_token = "valid_refresh_token"
        rt_id = self._insert_refresh_token(1, raw_token)
        request = mock_request_factory()
        await service.refresh(request, mock_response, raw_token)
        # Old token should be revoked
        assert svc_module._refresh_tokens[rt_id]["revoked_at"] is not None
        # New token should be issued
        assert len(svc_module._refresh_tokens) == 2

    @pytest.mark.anyio
    async def test_refresh_no_token_raises(self, service, mock_request_factory, mock_response):
        request = mock_request_factory()
        with pytest.raises(HTTPException) as exc:
            await service.refresh(request, mock_response, None)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "MISSING_REFRESH_TOKEN"

    @pytest.mark.anyio
    async def test_refresh_invalid_token_raises(self, service, mock_request_factory, mock_response):
        request = mock_request_factory()
        with pytest.raises(HTTPException) as exc:
            await service.refresh(request, mock_response, "nonexistent_token")
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "INVALID_REFRESH_TOKEN"

    @pytest.mark.anyio
    async def test_refresh_revoked_token_raises_and_revokes_all(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        raw_token = "revoked_refresh_token"
        self._insert_refresh_token(1, raw_token, revoked=True)
        # Insert another active token for same user
        self._insert_refresh_token(1, "other_token")
        request = mock_request_factory()
        with pytest.raises(HTTPException) as exc:
            await service.refresh(request, mock_response, raw_token)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "REFRESH_TOKEN_REUSE"
        # All tokens for user should be revoked
        for rt in svc_module._refresh_tokens.values():
            if rt["user_id"] == 1:
                assert rt["revoked_at"] is not None

    @pytest.mark.anyio
    async def test_refresh_expired_token_raises(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        raw_token = "expired_refresh_token"
        self._insert_refresh_token(1, raw_token, days_until_expiry=-1)  # expired
        request = mock_request_factory()
        with pytest.raises(HTTPException) as exc:
            await service.refresh(request, mock_response, raw_token)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "REFRESH_TOKEN_EXPIRED"

    @pytest.mark.anyio
    async def test_refresh_inactive_user_raises(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        # Mark user inactive
        for u in svc_module._users.values():
            u["is_active"] = False
        raw_token = "valid_refresh_token"
        self._insert_refresh_token(1, raw_token)
        request = mock_request_factory()
        with pytest.raises(HTTPException) as exc:
            await service.refresh(request, mock_response, raw_token)
        assert exc.value.status_code == 401
        assert exc.value.detail["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.anyio
    async def test_refresh_sets_new_cookie(self, service, mock_request_factory, mock_response):
        await service.register(make_register_body())
        raw_token = "valid_refresh_token"
        self._insert_refresh_token(1, raw_token)
        request = mock_request_factory()
        await service.refresh(request, mock_response, raw_token)
        mock_response.set_cookie.assert_called_once()


# ---------------------------------------------------------------------------
# Router-level integration tests via TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    from fastapi import FastAPI
    from app.auth.router import router
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def clear_stores_module(clear_stores):
    # clear_stores is already autouse; this just ensures ordering for module-scoped client
    pass


class TestRouterRegister:
    def test_register_201(self, client):
        resp = client.post("/auth/register", json={
            "fullName": "Jane Doe",
            "email": "jane@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "jane@example.com"
        assert "fullName" in data

    def test_register_duplicate_409(self, client):
        payload = {
            "fullName": "Jane Doe",
            "email": "dupcheck@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        }
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_password_mismatch_422(self, client):
        resp = client.post("/auth/register", json={
            "fullName": "Jane Doe",
            "email": "mismatch@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": "OtherPass1!",
        })
        assert resp.status_code == 422


class TestRouterLogin:
    def test_login_200(self, client):
        client.post("/auth/register", json={
            "fullName": "Login User",
            "email": "loginuser@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        })
        resp = client.post("/auth/login", json={
            "email": "loginuser@example.com",
            "password": VALID_PASSWORD,
        })
        assert resp.status_code == 200
        assert "accessToken" in resp.json()

    def test_login_invalid_credentials_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": VALID_PASSWORD,
        })
        assert resp.status_code == 401


class TestRouterForgotPassword:
    def test_forgot_password_202(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "anyemail@example.com"})
        assert resp.status_code == 202
        assert "message" in resp.json()


class TestRouterMe:
    def test_me_no_token_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_token_200(self, client):
        # Register then login to get a token
        client.post("/auth/register", json={
            "fullName": "Me User",
            "email": "meuser@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        })
        login_resp = client.post("/auth/login", json={
            "email": "meuser@example.com",
            "password": VALID_PASSWORD,
        })
        token = login_resp.json()["accessToken"]
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "meuser@example.com"


class TestRouterLogout:
    def test_logout_200(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 200
        assert "message" in resp.json()


class TestRouterRefresh:
    def test_refresh_no_cookie_401(self, client):
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_invalid_cookie_401(self, client):
        client.cookies.set("refresh_token", "bad_token_value")
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401
        client.cookies.clear()

    def test_refresh_valid_flow(self, client):
        # Register and login to get real refresh cookie
        client.post("/auth/register", json={
            "fullName": "Refresh User",
            "email": "refreshuser@example.com",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        })
        login_resp = client.post("/auth/login", json={
            "email": "refreshuser@example.com",
            "password": VALID_PASSWORD,
        })
        # TestClient should carry the Set-Cookie forward
        refresh_resp = client.post("/auth/refresh")
        assert refresh_resp.status_code == 200
        assert "accessToken" in refresh_resp.json()


class TestRouterResetPassword:
    def test_reset_password_invalid_token_400(self, client):
        resp = client.post("/auth/reset-password", json={
            "token": "faketoken",
            "password": VALID_PASSWORD,
            "confirmPassword": VALID_PASSWORD,
        })
        assert resp.status_code == 400
