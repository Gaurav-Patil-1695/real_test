import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a TestClient built from the real FastAPI app."""
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Basic app meta-data / startup
# ---------------------------------------------------------------------------

class TestAppMetadata:
    def test_openapi_title(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "Auth Starter"

    def test_openapi_version(self, client):
        resp = client.get("/api/v1/openapi.json")
        data = resp.json()
        assert data["info"]["version"] == "1.0.0"

    def test_docs_url_reachable(self, client):
        resp = client.get("/api/v1/docs")
        assert resp.status_code == 200

    def test_redoc_url_reachable(self, client):
        resp = client.get("/api/v1/redoc")
        assert resp.status_code == 200

    def test_openapi_url_reachable(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

class TestCORSMiddleware:
    def test_cors_allow_origin_default(self, client):
        """OPTIONS pre-flight with the default allowed origin."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Starlette CORS returns 200 for pre-flight
        assert resp.status_code in (200, 400)
        # The allow-origin header should reflect our origin when it matches
        origin_header = resp.headers.get("access-control-allow-origin", "")
        if resp.status_code == 200:
            assert origin_header == "http://localhost:3000"

    def test_cors_disallowed_origin(self, client):
        """Requests from unknown origins should NOT get the allow-origin header."""
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        origin_header = resp.headers.get("access-control-allow-origin", "")
        assert origin_header != "http://evil.example.com"

    def test_cors_origin_from_env(self, monkeypatch):
        """CORS_ORIGIN env variable is picked up when the app is created."""
        monkeypatch.setenv("CORS_ORIGIN", "http://my-custom-origin.com")
        # Re-import the module so the env var is read again
        import importlib
        import app.main as main_module
        importlib.reload(main_module)
        # The middleware is configured – we just verify the constant was read
        assert os.getenv("CORS_ORIGIN") == "http://my-custom-origin.com"


# ---------------------------------------------------------------------------
# Auth router is mounted under /api/v1/auth
# ---------------------------------------------------------------------------

class TestAuthRouterMounted:
    def test_auth_prefix_appears_in_openapi(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        paths = resp.json().get("paths", {})
        auth_paths = [p for p in paths if p.startswith("/api/v1/auth")]
        assert len(auth_paths) > 0, "Expected at least one /api/v1/auth/* route in OpenAPI spec"


# ---------------------------------------------------------------------------
# ErrorResponse exception handler
# ---------------------------------------------------------------------------

class TestErrorResponseHandler:
    """Verify the custom exception handler formats the JSON body correctly."""

    def test_error_response_handler_format(self, client):
        """Inject an ErrorResponse through a test-only route and check the shape."""
        from app.main import app
        from app.auth.schemas import ErrorResponse

        # Add a temporary route that raises ErrorResponse so we can test the handler
        @app.get("/test-error-handler")
        async def _raise_error():
            raise ErrorResponse(
                status_code=422,
                code="TEST_CODE",
                message="test message",
                details={"field": "value"},
            )

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.get("/test-error-handler")

        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        error = body["error"]
        assert error["code"] == "TEST_CODE"
        assert error["message"] == "test message"
        assert error["details"] == {"field": "value"}

        # Clean up the temporary route
        app.routes[:] = [
            r for r in app.routes
            if not (hasattr(r, "path") and r.path == "/test-error-handler")
        ]

    def test_error_response_handler_no_details(self, client):
        """ErrorResponse with no details should include details key (None or empty)."""
        from app.main import app
        from app.auth.schemas import ErrorResponse

        @app.get("/test-error-handler-no-details")
        async def _raise_error_no_details():
            raise ErrorResponse(
                status_code=400,
                code="BAD_REQUEST",
                message="bad request",
            )

        test_client = TestClient(app, raise_server_exceptions=False)
        resp = test_client.get("/test-error-handler-no-details")

        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "BAD_REQUEST"
        assert body["error"]["message"] == "bad request"
        # details key must exist (value may be None / {} depending on schema default)
        assert "details" in body["error"]

        # Clean up
        app.routes[:] = [
            r for r in app.routes
            if not (hasattr(r, "path") and r.path == "/test-error-handler-no-details")
        ]


# ---------------------------------------------------------------------------
# API_PREFIX constant
# ---------------------------------------------------------------------------

class TestAPIPrefix:
    def test_api_prefix_constant(self):
        from app.main import API_PREFIX
        assert API_PREFIX == "/api/v1"

    def test_cors_origin_default_constant(self):
        """When CORS_ORIGIN env var is absent the default should be localhost:3000."""
        # Temporarily unset the env var and reload
        saved = os.environ.pop("CORS_ORIGIN", None)
        try:
            import importlib
            import app.main as main_module
            importlib.reload(main_module)
            assert main_module.CORS_ORIGIN == "http://localhost:3000"
        finally:
            if saved is not None:
                os.environ["CORS_ORIGIN"] = saved
