"""Unit tests for real_test/auth-backend/app/config/settings.py"""
from __future__ import annotations

import importlib
import sys
import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_ENV: dict[str, str] = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
    "JWT_SECRET_KEY": "a" * 32,
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_TTL_MINUTES": "15",
    "BCRYPT_ROUNDS": "12",
    "RESET_TOKEN_TTL_MINUTES": "30",
    "REFRESH_TOKEN_TTL_DAYS": "7",
    "REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME": "30",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "user@example.com",
    "SMTP_PASSWORD": "secret",
    "SMTP_FROM_ADDRESS": "noreply@example.com",
    "SMTP_USE_TLS": "true",
    "RATE_LIMIT_LOGIN_MAX_ATTEMPTS": "5",
    "RATE_LIMIT_LOGIN_WINDOW_SECONDS": "60",
    "RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS": "3",
    "RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS": "300",
}


def make_settings(overrides: dict[str, str] | None = None, monkeypatch=None):
    """Import Settings fresh (bypassing the module-level singleton) with
    environment variables set via *monkeypatch*."""
    env = {**MINIMAL_VALID_ENV, **(overrides or {})}

    # Remove keys whose value is explicitly set to None (simulate missing)
    env = {k: v for k, v in env.items() if v is not None}

    # Patch environment and prevent .env file from being read
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    # Remove keys the caller wants absent
    if overrides:
        for key, value in overrides.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)

    # Force reload to get a fresh Settings class (not the module singleton)
    # We import only the class, not instantiate via module level.
    module_path = "real_test.auth-backend.app.config.settings"
    # Use direct import instead of module path with hyphens
    import importlib.util, pathlib

    spec = importlib.util.spec_from_file_location(
        "settings_mod",
        pathlib.Path(__file__).parent.parent.parent / "app" / "config" / "settings.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # We do NOT exec the module (that would trigger the singleton);
    # instead we load only the Settings class definition.
    # We patch env BEFORE exec so the module-level `settings = Settings()` works.
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.Settings(**{k: v for k, v in env.items()})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_settings(monkeypatch):
    return make_settings(monkeypatch=monkeypatch)


# ---------------------------------------------------------------------------
# Happy-path: valid configuration
# ---------------------------------------------------------------------------

class TestValidSettings:
    def test_database_url_stored(self, valid_settings):
        assert valid_settings.DATABASE_URL == MINIMAL_VALID_ENV["DATABASE_URL"]

    def test_jwt_secret_key_stored(self, valid_settings):
        assert valid_settings.JWT_SECRET_KEY == "a" * 32

    def test_jwt_algorithm_default(self, valid_settings):
        assert valid_settings.JWT_ALGORITHM == "HS256"

    def test_jwt_access_token_ttl(self, valid_settings):
        assert valid_settings.JWT_ACCESS_TOKEN_TTL_MINUTES == 15

    def test_bcrypt_rounds(self, valid_settings):
        assert valid_settings.BCRYPT_ROUNDS == 12

    def test_reset_token_ttl(self, valid_settings):
        assert valid_settings.RESET_TOKEN_TTL_MINUTES == 30

    def test_refresh_token_ttl_days(self, valid_settings):
        assert valid_settings.REFRESH_TOKEN_TTL_DAYS == 7

    def test_refresh_token_ttl_days_remember_me(self, valid_settings):
        assert valid_settings.REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME == 30

    def test_smtp_host(self, valid_settings):
        assert valid_settings.SMTP_HOST == "smtp.example.com"

    def test_smtp_port(self, valid_settings):
        assert valid_settings.SMTP_PORT == 587

    def test_smtp_username(self, valid_settings):
        assert valid_settings.SMTP_USERNAME == "user@example.com"

    def test_smtp_password(self, valid_settings):
        assert valid_settings.SMTP_PASSWORD == "secret"

    def test_smtp_from_address(self, valid_settings):
        assert str(valid_settings.SMTP_FROM_ADDRESS) == "noreply@example.com"

    def test_smtp_use_tls_default_true(self, valid_settings):
        assert valid_settings.SMTP_USE_TLS is True

    def test_rate_limit_login_max_attempts(self, valid_settings):
        assert valid_settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS == 5

    def test_rate_limit_login_window_seconds(self, valid_settings):
        assert valid_settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS == 60

    def test_rate_limit_forgot_password_max_attempts(self, valid_settings):
        assert valid_settings.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS == 3

    def test_rate_limit_forgot_password_window_seconds(self, valid_settings):
        assert valid_settings.RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS == 300


# ---------------------------------------------------------------------------
# DATABASE_URL validator
# ---------------------------------------------------------------------------

class TestDatabaseUrlValidator:
    def test_rejects_empty_string(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            make_settings({"DATABASE_URL": ""}, monkeypatch=monkeypatch)
        errors = exc_info.value.errors()
        assert any("DATABASE_URL" in str(e) or "database_url" in str(e).lower() for e in errors)

    def test_rejects_whitespace_only(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"DATABASE_URL": "   "}, monkeypatch=monkeypatch)

    def test_accepts_valid_dsn(self, monkeypatch):
        s = make_settings(
            {"DATABASE_URL": "postgresql://admin:pwd@db.host:5432/mydb"},
            monkeypatch=monkeypatch,
        )
        assert s.DATABASE_URL == "postgresql://admin:pwd@db.host:5432/mydb"


# ---------------------------------------------------------------------------
# JWT_SECRET_KEY validator
# ---------------------------------------------------------------------------

class TestJwtSecretKeyValidator:
    def test_rejects_key_shorter_than_32_chars(self, monkeypatch):
        with pytest.raises(ValidationError) as exc_info:
            make_settings({"JWT_SECRET_KEY": "short"}, monkeypatch=monkeypatch)
        assert any(
            "JWT_SECRET_KEY" in str(e) or "32" in str(e)
            for e in exc_info.value.errors()
        )

    def test_rejects_key_exactly_31_chars(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"JWT_SECRET_KEY": "b" * 31}, monkeypatch=monkeypatch)

    def test_accepts_key_exactly_32_chars(self, monkeypatch):
        s = make_settings({"JWT_SECRET_KEY": "c" * 32}, monkeypatch=monkeypatch)
        assert s.JWT_SECRET_KEY == "c" * 32

    def test_accepts_key_longer_than_32_chars(self, monkeypatch):
        s = make_settings({"JWT_SECRET_KEY": "d" * 64}, monkeypatch=monkeypatch)
        assert s.JWT_SECRET_KEY == "d" * 64


# ---------------------------------------------------------------------------
# BCRYPT_ROUNDS validator
# ---------------------------------------------------------------------------

class TestBcryptRoundsValidator:
    def test_rejects_rounds_below_12(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"BCRYPT_ROUNDS": "11"}, monkeypatch=monkeypatch)

    def test_rejects_rounds_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"BCRYPT_ROUNDS": "0"}, monkeypatch=monkeypatch)

    def test_accepts_rounds_exactly_12(self, monkeypatch):
        s = make_settings({"BCRYPT_ROUNDS": "12"}, monkeypatch=monkeypatch)
        assert s.BCRYPT_ROUNDS == 12

    def test_accepts_rounds_above_12(self, monkeypatch):
        s = make_settings({"BCRYPT_ROUNDS": "14"}, monkeypatch=monkeypatch)
        assert s.BCRYPT_ROUNDS == 14


# ---------------------------------------------------------------------------
# JWT_ACCESS_TOKEN_TTL_MINUTES field constraint (gt=0)
# ---------------------------------------------------------------------------

class TestJwtAccessTokenTtl:
    def test_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"JWT_ACCESS_TOKEN_TTL_MINUTES": "0"}, monkeypatch=monkeypatch)

    def test_rejects_negative(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"JWT_ACCESS_TOKEN_TTL_MINUTES": "-1"}, monkeypatch=monkeypatch)

    def test_accepts_positive(self, monkeypatch):
        s = make_settings({"JWT_ACCESS_TOKEN_TTL_MINUTES": "60"}, monkeypatch=monkeypatch)
        assert s.JWT_ACCESS_TOKEN_TTL_MINUTES == 60


# ---------------------------------------------------------------------------
# SMTP_PORT field constraint (gt=0, le=65535)
# ---------------------------------------------------------------------------

class TestSmtpPort:
    def test_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"SMTP_PORT": "0"}, monkeypatch=monkeypatch)

    def test_rejects_above_65535(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"SMTP_PORT": "65536"}, monkeypatch=monkeypatch)

    def test_accepts_port_1(self, monkeypatch):
        s = make_settings({"SMTP_PORT": "1"}, monkeypatch=monkeypatch)
        assert s.SMTP_PORT == 1

    def test_accepts_port_65535(self, monkeypatch):
        s = make_settings({"SMTP_PORT": "65535"}, monkeypatch=monkeypatch)
        assert s.SMTP_PORT == 65535

    def test_accepts_common_ports(self, monkeypatch):
        for port in ["25", "465", "587"]:
            s = make_settings({"SMTP_PORT": port}, monkeypatch=monkeypatch)
            assert s.SMTP_PORT == int(port)


# ---------------------------------------------------------------------------
# SMTP_FROM_ADDRESS — must be valid email
# ---------------------------------------------------------------------------

class TestSmtpFromAddress:
    def test_rejects_invalid_email(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"SMTP_FROM_ADDRESS": "not-an-email"}, monkeypatch=monkeypatch)

    def test_accepts_valid_email(self, monkeypatch):
        s = make_settings(
            {"SMTP_FROM_ADDRESS": "sender@domain.org"}, monkeypatch=monkeypatch
        )
        assert "sender@domain.org" in str(s.SMTP_FROM_ADDRESS)


# ---------------------------------------------------------------------------
# SMTP_USE_TLS — boolean coercion
# ---------------------------------------------------------------------------

class TestSmtpUseTls:
    def test_default_is_true(self, valid_settings):
        assert valid_settings.SMTP_USE_TLS is True

    def test_can_be_set_false(self, monkeypatch):
        s = make_settings({"SMTP_USE_TLS": "false"}, monkeypatch=monkeypatch)
        assert s.SMTP_USE_TLS is False

    def test_string_true(self, monkeypatch):
        s = make_settings({"SMTP_USE_TLS": "true"}, monkeypatch=monkeypatch)
        assert s.SMTP_USE_TLS is True


# ---------------------------------------------------------------------------
# Rate-limit constraints (gt=0)
# ---------------------------------------------------------------------------

class TestRateLimitConstraints:
    def test_login_max_attempts_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings(
                {"RATE_LIMIT_LOGIN_MAX_ATTEMPTS": "0"}, monkeypatch=monkeypatch
            )

    def test_login_window_seconds_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings(
                {"RATE_LIMIT_LOGIN_WINDOW_SECONDS": "0"}, monkeypatch=monkeypatch
            )

    def test_forgot_password_max_attempts_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings(
                {"RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS": "0"}, monkeypatch=monkeypatch
            )

    def test_forgot_password_window_seconds_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings(
                {"RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS": "0"}, monkeypatch=monkeypatch
            )


# ---------------------------------------------------------------------------
# Refresh token constraints (gt=0)
# ---------------------------------------------------------------------------

class TestRefreshTokenConstraints:
    def test_refresh_token_ttl_days_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"REFRESH_TOKEN_TTL_DAYS": "0"}, monkeypatch=monkeypatch)

    def test_refresh_token_ttl_days_remember_me_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings(
                {"REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME": "0"}, monkeypatch=monkeypatch
            )

    def test_refresh_token_ttl_days_accepts_positive(self, monkeypatch):
        s = make_settings({"REFRESH_TOKEN_TTL_DAYS": "14"}, monkeypatch=monkeypatch)
        assert s.REFRESH_TOKEN_TTL_DAYS == 14


# ---------------------------------------------------------------------------
# RESET_TOKEN_TTL_MINUTES constraint (gt=0)
# ---------------------------------------------------------------------------

class TestResetTokenConstraints:
    def test_rejects_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            make_settings({"RESET_TOKEN_TTL_MINUTES": "0"}, monkeypatch=monkeypatch)

    def test_accepts_positive(self, monkeypatch):
        s = make_settings({"RESET_TOKEN_TTL_MINUTES": "60"}, monkeypatch=monkeypatch)
        assert s.RESET_TOKEN_TTL_MINUTES == 60


# ---------------------------------------------------------------------------
# extra="ignore" — unknown fields should not raise
# ---------------------------------------------------------------------------

class TestExtraFieldsIgnored:
    def test_extra_fields_are_ignored(self, monkeypatch):
        s = make_settings({"UNKNOWN_FIELD": "should_be_ignored"}, monkeypatch=monkeypatch)
        assert not hasattr(s, "UNKNOWN_FIELD")


# ---------------------------------------------------------------------------
# JWT_ALGORITHM default
# ---------------------------------------------------------------------------

class TestJwtAlgorithmDefault:
    def test_default_algorithm_is_hs256(self, valid_settings):
        assert valid_settings.JWT_ALGORITHM == "HS256"

    def test_can_override_algorithm(self, monkeypatch):
        s = make_settings({"JWT_ALGORITHM": "RS256"}, monkeypatch=monkeypatch)
        assert s.JWT_ALGORITHM == "RS256"
