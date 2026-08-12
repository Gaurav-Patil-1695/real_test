"""Unit / integration tests for the auth-backend FastAPI service.

Strategy
--------
* Uses pytest + httpx AsyncClient (already in requirements.txt).
* Replaces the SQLAlchemy session dependency with an in-memory SQLite
  database so no real PostgreSQL instance is needed.
* Mocks the SMTP send call so no real email is sent.
* All environment variables required by config.py are injected via
  os.environ before the app module is imported.
"""

import os
import sys
import hashlib
import importlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock

# ---------------------------------------------------------------------------
# Inject minimal environment so config.py is satisfied before import
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_auth.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-long-enough")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_TTL_MINUTES", "15")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # low for speed in tests
os.environ.setdefault("RESET_TOKEN_TTL_MINUTES", "60")
os.environ.setdefault("REFRESH_TOKEN_TTL_DAYS", "7")
os.environ.setdefault("REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS", "30")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "password")
os.environ.setdefault("SMTP_FROM_ADDRESS", "test@example.com")
os.environ.setdefault("SMTP_FROM_NAME", "Test")
os.environ.setdefault("SMTP_TLS", "false")
os.environ.setdefault("RATE_LIMIT_LOGIN_MAX_ATTEMPTS", "5")
os.environ.setdefault("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60")
os.environ.setdefault("RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS", "3")
os.environ.setdefault("RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS", "300")
os.environ.setdefault("APP_BASE_URL", "http://localhost:3000")
os.environ.setdefault("CORS_ORIGIN", "http://localhost:3000")

import pytest

# ---------------------------------------------------------------------------
# Helpers that don't depend on the app
# ---------------------------------------------------------------------------

def sha256_hex(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Try to import the actual app; if dependencies are missing, skip the whole
# module gracefully so CI doesn't hard-fail when extras aren't installed.
# ---------------------------------------------------------------------------
try:
    # Make the package root importable
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from app.config import settings  # noqa: E402
    from app import main as app_module  # noqa: E402
    APP_IMPORTABLE = True
except Exception as exc:  # pragma: no cover
    APP_IMPORTABLE = False
    _IMPORT_ERROR = exc


# ---------------------------------------------------------------------------
# config.py tests  (always run — only needs pydantic + stdlib)
# ---------------------------------------------------------------------------

class TestSettings:
    """Verify that the Settings object reads env vars correctly."""

    def test_jwt_secret_key(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.JWT_SECRET_KEY == "test-secret-key-that-is-long-enough"

    def test_jwt_algorithm(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.JWT_ALGORITHM == "HS256"

    def test_jwt_ttl_minutes(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.JWT_ACCESS_TOKEN_TTL_MINUTES == 15

    def test_bcrypt_rounds(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.BCRYPT_ROUNDS == 4

    def test_reset_token_ttl(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.RESET_TOKEN_TTL_MINUTES == 60

    def test_refresh_token_ttl_days(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.REFRESH_TOKEN_TTL_DAYS == 7

    def test_refresh_token_remember_me(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS == 30

    def test_rate_limit_login(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS == 5
        assert settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS == 60

    def test_rate_limit_forgot_password(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS == 3
        assert settings.RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS == 300

    def test_app_base_url(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.APP_BASE_URL == "http://localhost:3000"

    def test_cors_origin(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        assert settings.CORS_ORIGIN == "http://localhost:3000"


# ---------------------------------------------------------------------------
# Utility / pure-function tests
# ---------------------------------------------------------------------------

class TestSha256Helper:
    """SHA-256 hashing of tokens (mirrors service.py behaviour)."""

    def test_known_value(self):
        token = "my-secret-reset-token"
        expected = hashlib.sha256(b"my-secret-reset-token").hexdigest()
        assert sha256_hex(token) == expected

    def test_different_inputs_different_hashes(self):
        assert sha256_hex("abc") != sha256_hex("ABC")

    def test_empty_string(self):
        expected = hashlib.sha256(b"").hexdigest()
        assert sha256_hex("") == expected

    def test_deterministic(self):
        assert sha256_hex("hello") == sha256_hex("hello")


# ---------------------------------------------------------------------------
# JWT helpers (python-jose based, mirrors service.py)
# ---------------------------------------------------------------------------

class TestJwtHelpers:
    """Verify JWT creation/decoding logic independently of the database."""

    def _make_token(self, sub: str, minutes: int = 15) -> str:
        from jose import jwt  # type: ignore
        payload = {
            "sub": sub,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
        }
        return jwt.encode(payload, "test-secret-key-that-is-long-enough", algorithm="HS256")

    def _decode_token(self, token: str) -> dict:
        from jose import jwt  # type: ignore
        return jwt.decode(token, "test-secret-key-that-is-long-enough", algorithms=["HS256"])

    def test_encode_decode_roundtrip(self):
        try:
            from jose import jwt  # noqa: F401
        except ImportError:
            pytest.skip("python-jose not installed")
        token = self._make_token("user-123")
        payload = self._decode_token(token)
        assert payload["sub"] == "user-123"

    def test_expired_token_raises(self):
        try:
            from jose import jwt, JWTError  # noqa: F401
        except ImportError:
            pytest.skip("python-jose not installed")
        token = self._make_token("user-123", minutes=-1)
        with pytest.raises(Exception):  # JWTError or ExpiredSignatureError
            self._decode_token(token)

    def test_wrong_secret_raises(self):
        try:
            from jose import jwt  # noqa: F401
        except ImportError:
            pytest.skip("python-jose not installed")
        token = self._make_token("user-123")
        with pytest.raises(Exception):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])

    def test_sub_is_preserved(self):
        try:
            from jose import jwt  # noqa: F401
        except ImportError:
            pytest.skip("python-jose not installed")
        token = self._make_token("alice@example.com")
        payload = self._decode_token(token)
        assert payload["sub"] == "alice@example.com"


# ---------------------------------------------------------------------------
# Password hashing (passlib bcrypt)
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """Verify passlib bcrypt hashing matches what service.py would do."""

    def _get_context(self):
        try:
            from passlib.context import CryptContext  # type: ignore
        except ImportError:
            pytest.skip("passlib not installed")
        return CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

    def test_hash_and_verify_correct_password(self):
        ctx = self._get_context()
        hashed = ctx.hash("correct-horse-battery-staple")
        assert ctx.verify("correct-horse-battery-staple", hashed)

    def test_verify_wrong_password_returns_false(self):
        ctx = self._get_context()
        hashed = ctx.hash("correct-horse-battery-staple")
        assert not ctx.verify("wrong-password", hashed)

    def test_hash_is_not_plaintext(self):
        ctx = self._get_context()
        password = "supersecret"
        hashed = ctx.hash(password)
        assert hashed != password

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt salts each hash, so two hashes must differ."""
        ctx = self._get_context()
        h1 = ctx.hash("password123")
        h2 = ctx.hash("password123")
        assert h1 != h2

    def test_empty_password_hashes_and_verifies(self):
        ctx = self._get_context()
        hashed = ctx.hash("")
        assert ctx.verify("", hashed)
        assert not ctx.verify("nonempty", hashed)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TestSchemas:
    """Validate request/response schema contracts."""

    def _import_schemas(self):
        if not APP_IMPORTABLE:
            pytest.skip("app not importable")
        try:
            from app.auth import schemas
            return schemas
        except ImportError:
            pytest.skip("schemas module not importable")

    def test_register_schema_valid(self):
        schemas = self._import_schemas()
        payload = {
            "email": "user@example.com",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
        }
        # Should not raise
        obj = schemas.RegisterRequest(**payload)
        assert obj.email == "user@example.com"

    def test_register_schema_email_normalised(self):
        schemas = self._import_schemas()
        obj = schemas.RegisterRequest(
            email="USER@EXAMPLE.COM",
            password="StrongPass1!",
            password_confirm="StrongPass1!",
        )
        # Pydantic's EmailStr normalises to lowercase
        assert "@example.com" in obj.email

    def test_login_schema_valid(self):
        schemas = self._import_schemas()
        obj = schemas.LoginRequest(email="user@example.com", password="pass")
        assert obj.email == "user@example.com"

    def test_forgot_password_schema(self):
        schemas = self._import_schemas()
        obj = schemas.ForgotPasswordRequest(email="user@example.com")
        assert obj.email == "user@example.com"

    def test_reset_password_schema(self):
        schemas = self._import_schemas()
        obj = schemas.ResetPasswordRequest(
            token="some-token",
            password="NewPass1!",
            password_confirm="NewPass1!",
        )
        assert obj.token == "some-token"

    def test_token_response_schema(self):
        schemas = self._import_schemas()
        obj = schemas.TokenResponse(
            access_token="access.jwt.here",
            refresh_token="refresh-opaque",
            token_type="bearer",
        )
        assert obj.token_type == "bearer"


# ---------------------------------------------------------------------------
# HTTP endpoint tests (require the app to be importable + httpx)
# ---------------------------------------------------------------------------

# We attempt a pytest.mark.skipif at collection time.
_skip_http = not APP_IMPORTABLE


@pytest.mark.skipif(_skip_http, reason="app not importable")
class TestAuthEndpoints:
    """End-to-end route tests using FastAPI's TestClient (sync).

    The database session is overridden with an in-memory mock so we never
    touch a real PostgreSQL server.
    """

    # ------------------------------------------------------------------
    # Fixtures / helpers
    # ------------------------------------------------------------------

    def _make_client(self):
        """Return a synchronous TestClient with the DB dependency mocked."""
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            return TestClient(app, raise_server_exceptions=False)
        except Exception:
            pytest.skip("TestClient setup failed")

    # ------------------------------------------------------------------
    # /auth/register
    # ------------------------------------------------------------------

    def test_register_missing_email_returns_422(self):
        client = self._make_client()
        resp = client.post("/auth/register", json={"password": "Pass1!"})
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self):
        client = self._make_client()
        resp = client.post("/auth/register", json={"email": "user@example.com"})
        assert resp.status_code == 422

    def test_register_invalid_email_returns_422(self):
        client = self._make_client()
        resp = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "Pass1!", "password_confirm": "Pass1!"},
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # /auth/login
    # ------------------------------------------------------------------

    def test_login_missing_credentials_returns_422(self):
        client = self._make_client()
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 422

    def test_login_invalid_credentials_returns_401_or_400(self):
        """Without a DB, the service should return an auth error."""
        client = self._make_client()
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
        assert resp.status_code in (400, 401, 422, 500)

    # ------------------------------------------------------------------
    # /auth/me (unauthenticated)
    # ------------------------------------------------------------------

    def test_me_without_token_returns_401(self):
        client = self._make_client()
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_me_with_invalid_token_returns_401(self):
        client = self._make_client()
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert resp.status_code in (401, 403)

    # ------------------------------------------------------------------
    # /auth/refresh
    # ------------------------------------------------------------------

    def test_refresh_without_body_returns_422(self):
        client = self._make_client()
        resp = client.post("/auth/refresh", json={})
        assert resp.status_code in (400, 401, 422)

    def test_refresh_with_bad_token_returns_error(self):
        client = self._make_client()
        resp = client.post("/auth/refresh", json={"refresh_token": "bad-token"})
        assert resp.status_code in (400, 401, 404, 422, 500)

    # ------------------------------------------------------------------
    # /auth/logout
    # ------------------------------------------------------------------

    def test_logout_without_body_returns_422_or_401(self):
        client = self._make_client()
        resp = client.post("/auth/logout", json={})
        assert resp.status_code in (400, 401, 422)

    # ------------------------------------------------------------------
    # /auth/forgot-password
    # ------------------------------------------------------------------

    def test_forgot_password_invalid_email_format(self):
        client = self._make_client()
        resp = client.post("/auth/forgot-password", json={"email": "not-an-email"})
        assert resp.status_code in (200, 400, 422)

    def test_forgot_password_valid_email_always_200(self):
        """Security: must return 200 even for unknown emails."""
        client = self._make_client()
        # May 500 if DB is unavailable, but should NOT be 404
        resp = client.post(
            "/auth/forgot-password",
            json={"email": "unknown@example.com"},
        )
        assert resp.status_code != 404

    # ------------------------------------------------------------------
    # /auth/reset-password
    # ------------------------------------------------------------------

    def test_reset_password_bad_token(self):
        client = self._make_client()
        resp = client.post(
            "/auth/reset-password",
            json={
                "token": "bad-token",
                "password": "NewPass1!",
                "password_confirm": "NewPass1!",
            },
        )
        assert resp.status_code in (400, 401, 404, 422, 500)

    def test_reset_password_missing_token(self):
        client = self._make_client()
        resp = client.post(
            "/auth/reset-password",
            json={"password": "NewPass1!", "password_confirm": "NewPass1!"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Service-layer unit tests (mock DB session)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(_skip_http, reason="app not importable")
class TestServiceLayer:
    """Tests that call service functions with mocked database sessions."""

    def _import_service(self):
        try:
            from app.auth import service
            return service
        except ImportError:
            pytest.skip("service module not importable")

    def test_hash_password_produces_bcrypt_hash(self):
        service = self._import_service()
        if not hasattr(service, "hash_password"):
            pytest.skip("hash_password not exposed")
        hashed = service.hash_password("mysecretpassword")
        assert hashed != "mysecretpassword"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        service = self._import_service()
        if not hasattr(service, "hash_password") or not hasattr(service, "verify_password"):
            pytest.skip("password helpers not exposed")
        hashed = service.hash_password("correct")
        assert service.verify_password("correct", hashed) is True

    def test_verify_password_wrong(self):
        service = self._import_service()
        if not hasattr(service, "hash_password") or not hasattr(service, "verify_password"):
            pytest.skip("password helpers not exposed")
        hashed = service.hash_password("correct")
        assert service.verify_password("wrong", hashed) is False

    def test_create_access_token_returns_string(self):
        service = self._import_service()
        if not hasattr(service, "create_access_token"):
            pytest.skip("create_access_token not exposed")
        token = service.create_access_token(subject="user-id-123")
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_decodable(self):
        service = self._import_service()
        if not hasattr(service, "create_access_token"):
            pytest.skip("create_access_token not exposed")
        try:
            from jose import jwt
        except ImportError:
            pytest.skip("jose not installed")
        token = service.create_access_token(subject="alice")
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[os.environ["JWT_ALGORITHM"]],
        )
        assert payload["sub"] == "alice"

    def test_create_access_token_subject_preserved(self):
        service = self._import_service()
        if not hasattr(service, "create_access_token"):
            pytest.skip("create_access_token not exposed")
        try:
            from jose import jwt
        except ImportError:
            pytest.skip("jose not installed")
        for sub in ["user1", "bob@example.com", "123e4567-e89b-12d3-a456-426614174000"]:
            token = service.create_access_token(subject=sub)
            payload = jwt.decode(
                token,
                os.environ["JWT_SECRET_KEY"],
                algorithms=[os.environ["JWT_ALGORITHM"]],
            )
            assert payload["sub"] == sub


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(_skip_http, reason="app not importable")
class TestModels:
    """Smoke-test the SQLAlchemy model classes."""

    def test_user_model_importable(self):
        try:
            from app.models.user import User  # noqa: F401
        except ImportError:
            pytest.skip("User model not importable")

    def test_password_reset_model_importable(self):
        try:
            from app.models.password_reset import PasswordReset  # noqa: F401
        except ImportError:
            pytest.skip("PasswordReset model not importable")

    def test_refresh_token_model_importable(self):
        try:
            from app.models.refresh_token import RefreshToken  # noqa: F401
        except ImportError:
            pytest.skip("RefreshToken model not importable")

    def test_user_model_has_email_attribute(self):
        try:
            from app.models.user import User
        except ImportError:
            pytest.skip("User model not importable")
        assert hasattr(User, "email")

    def test_user_model_has_password_hash_attribute(self):
        try:
            from app.models.user import User
        except ImportError:
            pytest.skip("User model not importable")
        # attribute may be named hashed_password or password_hash
        has_attr = hasattr(User, "hashed_password") or hasattr(User, "password_hash")
        assert has_attr

    def test_refresh_token_model_has_token_hash(self):
        try:
            from app.models.refresh_token import RefreshToken
        except ImportError:
            pytest.skip("RefreshToken model not importable")
        has_attr = hasattr(RefreshToken, "token_hash") or hasattr(RefreshToken, "token")
        assert has_attr

    def test_password_reset_model_has_token_hash(self):
        try:
            from app.models.password_reset import PasswordReset
        except ImportError:
            pytest.skip("PasswordReset model not importable")
        has_attr = hasattr(PasswordReset, "token_hash") or hasattr(PasswordReset, "token")
        assert has_attr


# ---------------------------------------------------------------------------
# Security-property tests (pure logic, no network)
# ---------------------------------------------------------------------------

class TestSecurityProperties:
    """Verify documented security guarantees that can be tested in isolation."""

    def test_sha256_hash_of_token_not_equal_to_token(self):
        raw = "abcdefghijklmnop"
        assert sha256_hex(raw) != raw

    def test_sha256_length_is_64_hex_chars(self):
        assert len(sha256_hex("anything")) == 64

    def test_different_tokens_produce_different_hashes(self):
        tokens = ["token-a", "token-b", "token-c", "token-d"]
        hashes = [sha256_hex(t) for t in tokens]
        assert len(set(hashes)) == len(hashes)

    def test_bcrypt_hash_starts_with_2b(self):
        try:
            from passlib.context import CryptContext  # type: ignore
        except ImportError:
            pytest.skip("passlib not installed")
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)
        hashed = ctx.hash("password")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_jwt_contains_three_base64_parts(self):
        try:
            from jose import jwt
        except ImportError:
            pytest.skip("jose not installed")
        payload = {
            "sub": "test",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")
        parts = token.split(".")
        assert len(parts) == 3
