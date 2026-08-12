import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config.settings import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    rounds: int = settings.BCRYPT_ROUNDS
    hashed: bytes = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=rounds))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# Token hashing (SHA-256)
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """Return the hex-encoded SHA-256 digest of a token string.

    Stored in the database so raw tokens never reach the data layer.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def compare_token(plain: str, stored_hash: str) -> bool:
    """Constant-time comparison of a raw token against its stored SHA-256 hash."""
    expected: str = hash_token(plain)
    return hmac.compare_digest(expected, stored_hash)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode and return a signed JWT access token.

    Args:
        subject: The ``sub`` claim — typically the user id as a string.
        extra_claims: Additional claims merged into the payload.
        expires_delta: Override for the token lifetime; defaults to
            ``settings.ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode and return a signed JWT refresh token.

    Args:
        subject: The ``sub`` claim — typically the user id as a string.
        expires_delta: Override for the token lifetime; defaults to
            ``settings.REFRESH_TOKEN_EXPIRE_DAYS``.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, returning its payload.

    Raises:
        jose.JWTError: If the token is invalid, expired, or has a bad signature.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode a JWT and assert it is an access token.

    Raises:
        jose.JWTError: If the token is not a valid access token.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Token type is not 'access'.")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode a JWT and assert it is a refresh token.

    Raises:
        jose.JWTError: If the token is not a valid refresh token.
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Token type is not 'refresh'.")
    return payload
