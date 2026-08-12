from __future__ import annotations

from pydantic import AnyUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = Field(..., description="PostgreSQL DSN used by SQLAlchemy")

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = Field(..., description="Secret key for signing JWTs")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = Field(
        ..., description="Access token lifetime in minutes", gt=0
    )

    # ------------------------------------------------------------------ #
    # Bcrypt
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = Field(
        ..., description="bcrypt work factor (≥ 12 required)", ge=12
    )

    # ------------------------------------------------------------------ #
    # Password-reset token
    # ------------------------------------------------------------------ #
    RESET_TOKEN_TTL_MINUTES: int = Field(
        ..., description="Password-reset token lifetime in minutes", gt=0
    )

    # ------------------------------------------------------------------ #
    # Refresh token
    # ------------------------------------------------------------------ #
    REFRESH_TOKEN_TTL_DAYS: int = Field(
        ..., description="Refresh token lifetime (standard) in days", gt=0
    )
    REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME: int = Field(
        ..., description="Refresh token lifetime (remember-me) in days", gt=0
    )

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = Field(..., description="SMTP server hostname")
    SMTP_PORT: int = Field(..., description="SMTP server port", gt=0, le=65535)
    SMTP_USERNAME: str = Field(..., description="SMTP authentication username")
    SMTP_PASSWORD: str = Field(..., description="SMTP authentication password")
    SMTP_FROM_ADDRESS: EmailStr = Field(
        ..., description="Envelope / From address for outgoing mail"
    )
    SMTP_USE_TLS: bool = Field(default=True, description="Use STARTTLS for SMTP")

    # ------------------------------------------------------------------ #
    # Rate limits
    # ------------------------------------------------------------------ #
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = Field(
        ..., description="Max login attempts per window", gt=0
    )
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(
        ..., description="Login rate-limit window in seconds", gt=0
    )
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = Field(
        ..., description="Max forgot-password attempts per window", gt=0
    )
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = Field(
        ..., description="Forgot-password rate-limit window in seconds", gt=0
    )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_be_set(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must not be empty")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_have_minimum_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters for adequate security"
            )
        return v

    @field_validator("BCRYPT_ROUNDS")
    @classmethod
    def bcrypt_rounds_minimum(cls, v: int) -> int:
        if v < 12:
            raise ValueError("BCRYPT_ROUNDS must be >= 12 per security policy")
        return v


# Instantiate once at import time — any missing / invalid var raises immediately.
settings: Settings = Settings()
