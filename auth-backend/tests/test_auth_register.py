"""Unit tests for the /auth/register endpoint and AuthService.register method."""
import importlib
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# We need to reset the in-memory stores between tests so that state does not
# leak across test cases. We also need the app to be importable.
# ---------------------------------------------------------------------------

# Ensure the package root is on sys.path
import os

SRC_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SRC_ROOT))

# Import service module so we can manipulate globals
import app.auth.service as service_module
from app.auth.schemas import RegisterRequest, RegisterResponse
from app.auth.service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_stores():
    """Reset all in-memory stores and counters to a clean state."""
    service_module._users.clear()
    service_module._password_resets.clear()
    service_module._refresh_tokens.clear()
    service_module._user_id_counter = 0
    service_module._pr_id_counter = 0
    service_module._rt_id_counter = 0


def _make_register_body(
    full_name="Alice Smith",
    email="alice@example.com",
    password="Passw0rd!",
    confirm_password="Passw0rd!",
) -> RegisterRequest:
    return RegisterRequest(
        fullName=full_name,
        email=email,
        password=password,
        confirmPassword=confirm_password,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_stores():
    """Automatically reset in-memory stores before every test."""
    _reset_stores()
    yield
    _reset_stores()


@pytest.fixture()
def auth_service() -> AuthService:
    return AuthService()


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the whole application."""
    from fastapi import FastAPI
    from app.auth.router import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ===========================================================================
# Service-level unit tests
# ===========================================================================

class TestRegisterService:
    """Direct tests of AuthService.register()"""

    @pytest.mark.asyncio
    async def test_register_success_returns_response(self, auth_service):
        body = _make_register_body()
        result = await auth_service.register(body)

        assert isinstance(result, RegisterResponse)
        assert result.email == "alice@example.com"
        assert result.full_name == "Alice Smith"
        assert isinstance(result.id, int)
        assert result.id > 0
        # created_at should be an ISO-formatted string
        assert isinstance(result.created_at, str)
        assert "T" in result.created_at or "-" in result.created_at

    @pytest.mark.asyncio
    async def test_register_increments_user_id(self, auth_service):
        body1 = _make_register_body(email="a@example.com")
        body2 = _make_register_body(email="b@example.com")
        r1 = await auth_service.register(body1)
        r2 = await auth_service.register(body2)
        assert r2.id == r1.id + 1

    @pytest.mark.asyncio
    async def test_register_stores_user_in_memory(self, auth_service):
        body = _make_register_body()
        result = await auth_service.register(body)
        assert result.id in service_module._users
        stored = service_module._users[result.id]
        assert stored["email"] == body.email
        assert stored["full_name"] == body.full_name
        assert stored["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_password_hashed_not_stored_plaintext(self, auth_service):
        body = _make_register_body()
        result = await auth_service.register(body)
        stored = service_module._users[result.id]
        assert stored["password_hash"] != body.password
        # bcrypt hash starts with $2b$
        assert stored["password_hash"].startswith("$2")

    @pytest.mark.asyncio
    async def test_register_password_mismatch_raises_422(self, auth_service):
        body = _make_register_body(confirm_password="Differ3nt!")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error"]["code"] == "PASSWORD_MISMATCH"
        assert "match" in detail["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_409(self, auth_service):
        body = _make_register_body()
        await auth_service.register(body)
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"]["code"] == "EMAIL_TAKEN"

    # ---- Password strength validation ------------------------------------

    @pytest.mark.asyncio
    async def test_register_short_password_raises_422(self, auth_service):
        body = _make_register_body(password="Ab1!", confirm_password="Ab1!")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"

    @pytest.mark.asyncio
    async def test_register_no_uppercase_raises_422(self, auth_service):
        body = _make_register_body(password="passw0rd!", confirm_password="passw0rd!")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error"]["code"] == "WEAK_PASSWORD"
        assert any("uppercase" in e.lower() for e in detail["error"]["details"])

    @pytest.mark.asyncio
    async def test_register_no_lowercase_raises_422(self, auth_service):
        body = _make_register_body(password="PASSW0RD!", confirm_password="PASSW0RD!")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"
        details = exc_info.value.detail["error"]["details"]
        assert any("lowercase" in e.lower() for e in details)

    @pytest.mark.asyncio
    async def test_register_no_digit_raises_422(self, auth_service):
        body = _make_register_body(password="Password!", confirm_password="Password!")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"]["code"] == "WEAK_PASSWORD"
        details = exc_info.value.detail["error"]["details"]
        assert any("number" in e.lower() for e in details)

    @pytest.mark.asyncio
    async def test_register_mismatch_checked_before_strength(self, auth_service):
        """Password mismatch should be reported even if password is weak."""
        body = _make_register_body(password="weak", confirm_password="different")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(body)
        assert exc_info.value.detail["error"]["code"] == "PASSWORD_MISMATCH"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_case_sensitive(self, auth_service):
        """Email lookup is case-sensitive per the implementation."""
        body_lower = _make_register_body(email="alice@example.com")
        body_upper = _make_register_body(email="ALICE@example.com")
        await auth_service.register(body_lower)
        # Upper-case version should not collide (implementation does == comparison)
        result = await auth_service.register(body_upper)
        assert result.email == "ALICE@example.com"

    @pytest.mark.asyncio
    async def test_register_response_created_at_is_iso_string(self, auth_service):
        body = _make_register_body()
        result = await auth_service.register(body)
        # Must be parseable as ISO 8601
        from datetime import datetime
        dt = datetime.fromisoformat(result.created_at)
        assert dt is not None

    @pytest.mark.asyncio
    async def test_register_multiple_users_isolated(self, auth_service):
        emails = [f"user{i}@example.com" for i in range(5)]
        ids = []
        for email in emails:
            r = await auth_service.register(_make_register_body(email=email))
            ids.append(r.id)
        assert len(set(ids)) == 5, "Each user should get a unique id"


# ===========================================================================
# Router / HTTP integration tests (via FastAPI TestClient)
# ===========================================================================

class TestRegisterEndpoint:
    """Integration tests that go through the HTTP router."""

    def test_register_201_on_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Bob Builder",
                "email": "bob@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "bob@example.com"
        assert data["fullName"] == "Bob Builder"
        assert "id" in data
        assert "createdAt" in data

    def test_register_422_on_password_mismatch(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Charlie",
                "email": "charlie@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Wrong0rd!",
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["detail"]["error"]["code"] == "PASSWORD_MISMATCH"

    def test_register_409_on_duplicate_email(self, client):
        payload = {
            "fullName": "Dave",
            "email": "dave@example.com",
            "password": "Passw0rd!",
            "confirmPassword": "Passw0rd!",
        }
        r1 = client.post("/auth/register", json=payload)
        assert r1.status_code == 201
        r2 = client.post("/auth/register", json=payload)
        assert r2.status_code == 409
        assert r2.json()["detail"]["error"]["code"] == "EMAIL_TAKEN"

    def test_register_422_on_weak_password_too_short(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Eve",
                "email": "eve@example.com",
                "password": "Ab1",
                "confirmPassword": "Ab1",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "WEAK_PASSWORD"

    def test_register_422_on_weak_password_no_digit(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Frank",
                "email": "frank@example.com",
                "password": "Password!",
                "confirmPassword": "Password!",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "WEAK_PASSWORD"

    def test_register_422_on_weak_password_no_uppercase(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Grace",
                "email": "grace@example.com",
                "password": "passw0rd!",
                "confirmPassword": "passw0rd!",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "WEAK_PASSWORD"

    def test_register_422_on_weak_password_no_lowercase(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Hank",
                "email": "hank@example.com",
                "password": "PASSW0RD!",
                "confirmPassword": "PASSW0RD!",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "WEAK_PASSWORD"

    def test_register_422_on_invalid_email(self, client):
        """FastAPI/Pydantic validation should reject a bad email before our service."""
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Ivan",
                "email": "not-an-email",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        # Pydantic will return 422 for an invalid EmailStr
        assert resp.status_code == 422

    def test_register_422_on_missing_full_name(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "email": "judy@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        assert resp.status_code == 422

    def test_register_response_schema(self, client):
        """Ensure response conforms to RegisterResponse schema fields."""
        resp = client.post(
            "/auth/register",
            json={
                "fullName": "Karl",
                "email": "karl@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        required_fields = {"id", "fullName", "email", "createdAt"}
        assert required_fields.issubset(data.keys()), (
            f"Missing fields: {required_fields - data.keys()}"
        )

    def test_register_sequential_ids(self, client):
        """IDs issued to successive registrations should differ."""
        r1 = client.post(
            "/auth/register",
            json={
                "fullName": "Laura",
                "email": "laura@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        r2 = client.post(
            "/auth/register",
            json={
                "fullName": "Mike",
                "email": "mike@example.com",
                "password": "Passw0rd!",
                "confirmPassword": "Passw0rd!",
            },
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]
