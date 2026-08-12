from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config.settings import settings

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

# Access token is always short-lived regardless of rememberMe
ACCESS_TOKEN_TTL: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

# Refresh token TTL varies based on rememberMe flag
REFRESH_TOKEN_TTL_DEFAULT: timedelta = timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
REFRESH_TOKEN_TTL_EXTENDED: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME)

# Password reset token TTL
RESET_TOKEN_TTL: timedelta = timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

# ---------------------------------------------------------------------------
# Raw token generation
# ---------------------------------------------------------------------------

def _generate_opaque_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe opaque token string."""
    return secrets.token_urlsafe(nbytes)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*.

    Used to store refresh and reset tokens safely in the database.
    Comparison is always done by hashing the incoming value and comparing
    the digest — never storing or comparing plaintext.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Access tokens (JWT)
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """Create a short-lived JWT access token for *user_id*.

    Claims:
        sub  -- str(user_id)
        exp  -- UTC expiry timestamp
        iat  -- UTC issued-at timestamp
        type -- "access"
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + ACCESS_TOKEN_TTL
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token.

    Returns the payload dict on success, or *None* if the token is invalid
    or expired.  Callers must check the ``type`` claim.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Refresh tokens (opaque, stored hashed)
# ---------------------------------------------------------------------------

def create_refresh_token(remember_me: bool = False) -> tuple[str, str, datetime]:
    """Generate a new opaque refresh token.

    Args:
        remember_me: When *True* the token uses the extended TTL.

    Returns:
        A 3-tuple of:
          - raw_token   : the plaintext token to send to the client
          - token_hash  : SHA-256 digest to persist in the database
          - expires_at  : aware UTC datetime when the token expires
    """
    ttl = REFRESH_TOKEN_TTL_EXTENDED if remember_me else REFRESH_TOKEN_TTL_DEFAULT
    raw_token = _generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(tz=timezone.utc) + ttl
    return raw_token, token_hash, expires_at


def is_refresh_token_valid(token_row: dict) -> bool:
    """Return True if the token row is neither revoked nor expired."""
    if token_row.get("revoked_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    # Ensure comparison is timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc) < expires_at


# ---------------------------------------------------------------------------
# Refresh token rotation
# ---------------------------------------------------------------------------

def rotate_refresh_token(old_token_row: dict) -> tuple[str, str, datetime]:
    """Issue a replacement refresh token that preserves the rememberMe flag.

    The caller is responsible for revoking *old_token_row* in the database
    and persisting the returned token hash with the returned expiry.

    Returns:
        A 3-tuple of (raw_token, token_hash, expires_at) — same contract as
        :func:`create_refresh_token`.
    """
    remember_me: bool = bool(old_token_row.get("remember_me", False))
    return create_refresh_token(remember_me=remember_me)


# ---------------------------------------------------------------------------
# Password reset tokens (opaque, stored hashed)
# ---------------------------------------------------------------------------

def create_reset_token() -> tuple[str, str, datetime]:
    """Generate a one-time password-reset token.

    Returns:
        A 3-tuple of:
          - raw_token   : the plaintext token to embed in the email link
          - token_hash  : SHA-256 digest to persist in the database
          - expires_at  : aware UTC datetime when the token expires
    """
    raw_token = _generate_opaque_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(tz=timezone.utc) + RESET_TOKEN_TTL
    return raw_token, token_hash, expires_at


def is_reset_token_valid(token_row: dict) -> bool:
    """Return True if the reset token has not been used and has not expired."""
    if token_row.get("used_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc) < expires_at
