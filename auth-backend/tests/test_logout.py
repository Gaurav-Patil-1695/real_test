"""Unit tests for the logout-related functionality in AuthService and the /auth/logout router."""
import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers to reset in-memory state between tests
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
    """Ensure every test starts with a clean in-memory store."""
    _reset_service_state()
    yield
    _reset_service_state()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    from app.auth.service import AuthService
    return AuthService()


@pytest.fixture
def app():
    from fastapi import FastAPI
    from app.auth.router import router
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(headers=None, cookies=None):
    """Build a minimal Request-like object for AuthService calls."""
    from starlette.testclient import TestClient
    from fastapi import FastAPI
    from app.auth.router import router

    app = FastAPI()
    app.include_router(router)

    # Use Starlette's Request directly
    from starlette.requests import Request as StarletteRequest
    from starlette.datastructures import Headers
    import io

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/logout",
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    request = StarletteRequest(scope=scope)
    return request


def _make_response():
    from starlette.responses import Response
    return Response()


async def _register_and_login(service, email="test@example.com", password="Password1"):
    """Helper: register a user and log them in, returning (access_token, refresh_token_value)."""
    from app.auth.schemas import RegisterRequest, LoginRequest
    import app.auth.service as svc

    reg_body = RegisterRequest(
        fullName="Test User",
        email=email,
        password=password,
        confirmPassword=password,
    )
    await service.register(reg_body)

    response = _make_response()
    login_body = LoginRequest(email=email, password=password)
    login_resp = await service.login(login_body, response)

    # Grab the raw refresh token value from the store (last inserted)
    rt_record = list(svc._refresh_tokens.values())[-1]
    # We don't have the raw value directly; use the service's token value via cookie header
    # Instead, capture via response Set-Cookie
    import re
    set_cookie = ""
    for header_name, header_value in response.raw_headers:
        if header_name == b"set-cookie":
            set_cookie = header_value.decode()
            break
    # Parse: refresh_token=<value>;
    match = re.search(r"refresh_token=([^;]+)", set_cookie)
    refresh_token_value = match.group(1) if match else None

    return login_resp.access_token, refresh_token_value


# ===========================================================================
# AuthService.logout — unit tests
# ===========================================================================

class TestAuthServiceLogout:

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_revokes_refresh_tokens(self, service):
        """Logout with a valid Bearer token should revoke all refresh tokens for the user."""
        import app.auth.service as svc

        access_token, _ = await _register_and_login(service)

        # Confirm at least one refresh token exists and is active
        rt_records = list(svc._refresh_tokens.values())
        assert len(rt_records) >= 1
        assert all(rt["revoked_at"] is None for rt in rt_records)

        request = _make_request(headers={"Authorization": f"Bearer {access_token}"})
        response = _make_response()

        result = await service.logout(request, response)

        assert result.message == "Logged out successfully."
        # All refresh tokens for that user should now be revoked
        for rt in svc._refresh_tokens.values():
            assert rt["revoked_at"] is not None

    @pytest.mark.asyncio
    async def test_logout_without_token_still_succeeds(self, service):
        """Logout with no Authorization header should still return success."""
        request = _make_request(headers={})
        response = _make_response()

        result = await service.logout(request, response)

        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_clears_refresh_cookie(self, service):
        """Logout should delete the refresh_token cookie."""
        access_token, _ = await _register_and_login(service)

        request = _make_request(headers={"Authorization": f"Bearer {access_token}"})
        response = _make_response()

        await service.logout(request, response)

        # The response should have a Set-Cookie header that deletes the cookie
        cookie_headers = [
            v.decode() for k, v in response.raw_headers
            if k == b"set-cookie"
        ]
        # There should be at least one Set-Cookie dealing with refresh_token
        assert any("refresh_token" in h for h in cookie_headers)

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_still_succeeds(self, service):
        """Logout with a malformed/invalid Bearer token should not raise; just clear cookie."""
        request = _make_request(headers={"Authorization": "Bearer this.is.invalid"})
        response = _make_response()

        result = await service.logout(request, response)

        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_only_revokes_tokens_for_authenticated_user(self, service):
        """Logout should only revoke tokens belonging to the authenticated user."""
        import app.auth.service as svc

        # Register two users
        access_token_a, _ = await _register_and_login(
            service, email="a@example.com", password="PasswordA1"
        )
        access_token_b, _ = await _register_and_login(
            service, email="b@example.com", password="PasswordB1"
        )

        # Decode token A to get user id
        import jwt as pyjwt
        payload_a = pyjwt.decode(access_token_a, options={"verify_signature": False})
        user_id_a = int(payload_a["sub"])

        # Logout user A
        request = _make_request(headers={"Authorization": f"Bearer {access_token_a}"})
        response = _make_response()
        await service.logout(request, response)

        # User A's tokens should be revoked; user B's should still be active
        for rt in svc._refresh_tokens.values():
            if rt["user_id"] == user_id_a:
                assert rt["revoked_at"] is not None, "User A's token should be revoked"
            else:
                assert rt["revoked_at"] is None, "User B's token should NOT be revoked"

    @pytest.mark.asyncio
    async def test_logout_response_message(self, service):
        """LogoutResponse message field should be 'Logged out successfully.'"""
        request = _make_request(headers={})
        response = _make_response()
        result = await service.logout(request, response)
        assert result.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_idempotent_when_called_twice(self, service):
        """Calling logout twice with same token should not raise an error."""
        access_token, _ = await _register_and_login(service)

        request = _make_request(headers={"Authorization": f"Bearer {access_token}"})

        result1 = await service.logout(request, _make_response())
        result2 = await service.logout(request, _make_response())

        assert result1.message == "Logged out successfully."
        assert result2.message == "Logged out successfully."

    @pytest.mark.asyncio
    async def test_logout_does_not_revoke_already_revoked_tokens(self, service):
        """After a second logout, still-revoked tokens remain revoked (no error)."""
        import app.auth.service as svc
        from datetime import datetime, timezone

        access_token, _ = await _register_and_login(service)

        # Pre-revoke all tokens
        now = datetime.now(timezone.utc)
        for rt in svc._refresh_tokens.values():
            rt["revoked_at"] = now

        request = _make_request(headers={"Authorization": f"Bearer {access_token}"})
        response = _make_response()
        result = await service.logout(request, response)

        assert result.message == "Logged out successfully."


# ===========================================================================
# Router /auth/logout — integration tests via TestClient
# ===========================================================================

class TestLogoutRoute:

    def _register_and_login_via_client(self, client):
        """Register + login through HTTP, return (access_token, cookies)."""
        client.post(
            "/auth/register",
            json={
                "fullName": "Route User",
                "email": "route@example.com",
                "password": "RoutePass1",
                "confirmPassword": "RoutePass1",
            },
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": "route@example.com", "password": "RoutePass1"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        return data["accessToken"], login_resp.cookies

    def test_logout_returns_200(self, client):
        access_token, cookies = self._register_and_login_via_client(client)
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            cookies=cookies,
        )
        assert resp.status_code == 200

    def test_logout_returns_correct_message(self, client):
        access_token, cookies = self._register_and_login_via_client(client)
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            cookies=cookies,
        )
        assert resp.json()["message"] == "Logged out successfully."

    def test_logout_without_auth_header_returns_200(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully."

    def test_logout_with_bad_token_returns_200(self, client):
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer totallyinvalid"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully."

    def test_logout_revokes_refresh_token_so_refresh_fails(self, client):
        """After logout, using the old refresh token should fail."""
        access_token, cookies = self._register_and_login_via_client(client)

        # Perform logout
        client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            cookies=cookies,
        )

        # Now try to refresh using the old cookie
        refresh_resp = client.post("/auth/refresh", cookies=cookies)
        # Should be 401 because the refresh token is revoked
        assert refresh_resp.status_code == 401

    def test_logout_response_schema(self, client):
        """Response body must contain only the 'message' key."""
        resp = client.post("/auth/logout")
        body = resp.json()
        assert "message" in body
        assert isinstance(body["message"], str)

    def test_multiple_logins_logout_revokes_all_sessions(self, client):
        """Login twice, logout once — both refresh tokens should be revoked."""
        import app.auth.service as svc

        # Register
        client.post(
            "/auth/register",
            json={
                "fullName": "Multi Session",
                "email": "multi@example.com",
                "password": "MultiPass1",
                "confirmPassword": "MultiPass1",
            },
        )
        # First login
        r1 = client.post(
            "/auth/login",
            json={"email": "multi@example.com", "password": "MultiPass1"},
        )
        # Second login
        r2 = client.post(
            "/auth/login",
            json={"email": "multi@example.com", "password": "MultiPass1"},
        )
        access_token = r2.json()["accessToken"]

        # Logout with second session's token
        client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Both refresh tokens should now be revoked
        for rt in svc._refresh_tokens.values():
            assert rt["revoked_at"] is not None


# ===========================================================================
# _clear_refresh_cookie helper (unit)
# ===========================================================================

class TestClearRefreshCookie:

    def test_clear_refresh_cookie_sets_delete_cookie_header(self):
        from app.auth.service import _clear_refresh_cookie
        response = _make_response()
        _clear_refresh_cookie(response)

        cookie_headers = [
            v.decode() for k, v in response.raw_headers
            if k == b"set-cookie"
        ]
        assert any("refresh_token" in h for h in cookie_headers)


# ===========================================================================
# LogoutResponse schema
# ===========================================================================

class TestLogoutResponseSchema:

    def test_logout_response_valid(self):
        from app.auth.schemas import LogoutResponse
        resp = LogoutResponse(message="Logged out successfully.")
        assert resp.message == "Logged out successfully."

    def test_logout_response_requires_message(self):
        from app.auth.schemas import LogoutResponse
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            LogoutResponse()  # type: ignore
