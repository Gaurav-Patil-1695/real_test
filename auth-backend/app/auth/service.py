import hashlib
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.getenv("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))

# In-memory stores (replace with real DB repositories in production)
_users: dict[str, dict] = {}
_password_resets: dict[str, dict] = {}
_refresh_tokens: dict[str, dict] = {}


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return str(uuid.uuid4()) + "-" + os.urandom(32).hex()


def _create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired.",
                    "details": {},
                }
            },
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_INVALID",
                    "message": "Invalid token.",
                    "details": {},
                }
            },
        )


def _validate_password_policy(password: str) -> list[str]:
    """Return list of violated rule messages (verbatim from validation-rules.json)."""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
    return errors


class AuthService:
    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        errors: dict[str, str] = {}

        # Full name validation
        if not payload.fullName or not payload.fullName.strip():
            errors["fullName"] = "Full name is required."
        elif len(payload.fullName.strip()) < 2:
            errors["fullName"] = "Full name must be at least 2 characters."
        elif len(payload.fullName.strip()) > 100:
            errors["fullName"] = "Full name must be at most 100 characters."

        # Email validation
        if not payload.email or not payload.email.strip():
            errors["email"] = "Email is required."
        else:
            email_lower = payload.email.strip().lower()
            email_pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
            if not email_pattern.match(email_lower):
                errors["email"] = "Enter a valid email address."
            else:
                # Enumeration-resistant: check duplicate only if format valid
                if any(
                    u["email"] == email_lower for u in _users.values()
                ):
                    errors["email"] = "An account with this email already exists."

        # Password validation
        if not payload.password:
            errors["password"] = "Password is required."
        else:
            policy_errors = _validate_password_policy(payload.password)
            if policy_errors:
                errors["password"] = policy_errors[0]

        # Confirm password validation
        if not payload.confirmPassword:
            errors["confirmPassword"] = "Please confirm your password."
        elif payload.password and payload.confirmPassword != payload.password:
            errors["confirmPassword"] = "Passwords do not match."

        # Terms validation
        if not payload.acceptTerms:
            errors["acceptTerms"] = "You must accept the Terms of Service and Privacy Policy."

        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": errors,
                    }
                },
            )

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        email_lower = payload.email.strip().lower()
        full_name = payload.fullName.strip()

        _users[user_id] = {
            "id": user_id,
            "full_name": full_name,
            "email": email_lower,
            "password_hash": _hash_password(payload.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        access_token = _create_access_token(user_id, email_lower)
        refresh_raw = _generate_token()
        refresh_hash = _sha256(refresh_raw)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        _refresh_tokens[refresh_hash] = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_hash": refresh_hash,
            "expires_at": refresh_expires,
            "revoked_at": None,
            "remember_me": False,
            "created_at": now,
        }

        return RegisterResponse(
            accessToken=access_token,
            refreshToken=refresh_raw,
            user={
                "id": user_id,
                "fullName": full_name,
                "email": email_lower,
            },
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        invalid_msg = "Invalid email or password."

        if not payload.email or not payload.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": invalid_msg,
                        "details": {},
                    }
                },
            )

        email_lower = payload.email.strip().lower()
        user = next(
            (u for u in _users.values() if u["email"] == email_lower), None
        )

        if user is None or not _verify_password(payload.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": invalid_msg,
                        "details": {},
                    }
                },
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": invalid_msg,
                        "details": {},
                    }
                },
            )

        access_token = _create_access_token(user["id"], user["email"])
        refresh_raw = _generate_token()
        refresh_hash = _sha256(refresh_raw)
        remember = payload.rememberMe if payload.rememberMe is not None else False
        refresh_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=refresh_days)
        now = datetime.now(timezone.utc)

        _refresh_tokens[refresh_hash] = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "token_hash": refresh_hash,
            "expires_at": refresh_expires,
            "revoked_at": None,
            "remember_me": remember,
            "created_at": now,
        }

        return LoginResponse(
            accessToken=access_token,
            refreshToken=refresh_raw,
            user={
                "id": user["id"],
                "fullName": user["full_name"],
                "email": user["email"],
            },
        )

    async def forgotPassword(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        generic_message = (
            "If an account with that email exists, a password reset link has been sent."
        )

        if payload.email:
            email_lower = payload.email.strip().lower()
            user = next(
                (u for u in _users.values() if u["email"] == email_lower), None
            )
            if user:
                raw_token = _generate_token()
                token_hash = _sha256(raw_token)
                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

                _password_resets[token_hash] = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "used_at": None,
                    "created_at": now,
                }
                # In production: send email with raw_token

        return ForgotPasswordResponse(message=generic_message)

    async def resetPassword(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        errors: dict[str, str] = {}

        if not payload.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Password reset token is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        if not payload.password:
            errors["password"] = "Password is required."
        else:
            policy_errors = _validate_password_policy(payload.password)
            if policy_errors:
                errors["password"] = policy_errors[0]

        if not payload.confirmPassword:
            errors["confirmPassword"] = "Please confirm your password."
        elif payload.password and payload.confirmPassword != payload.password:
            errors["confirmPassword"] = "Passwords do not match."

        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Validation failed.",
                        "details": errors,
                    }
                },
            )

        token_hash = _sha256(payload.token)
        reset_record = _password_resets.get(token_hash)

        if reset_record is None or reset_record["used_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Password reset token is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        if datetime.now(timezone.utc) > reset_record["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Password reset token is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        user_id = reset_record["user_id"]
        user = _users.get(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Password reset token is invalid or has expired.",
                        "details": {},
                    }
                },
            )

        user["password_hash"] = _hash_password(payload.password)
        user["updated_at"] = datetime.now(timezone.utc)
        reset_record["used_at"] = datetime.now(timezone.utc)

        # Revoke all refresh tokens for this user
        now = datetime.now(timezone.utc)
        for rt in _refresh_tokens.values():
            if rt["user_id"] == user_id and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self) -> MeResponse:
        # In production, extract user from Authorization header/JWT
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required.",
                    "details": {},
                }
            },
        )

    async def logout(self, payload: LogoutRequest) -> LogoutResponse:
        if payload.refreshToken:
            token_hash = _sha256(payload.refreshToken)
            rt = _refresh_tokens.get(token_hash)
            if rt and rt["revoked_at"] is None:
                rt["revoked_at"] = datetime.now(timezone.utc)

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self, payload: RefreshRequest) -> RefreshResponse:
        if not payload.refreshToken:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )

        token_hash = _sha256(payload.refreshToken)
        rt = _refresh_tokens.get(token_hash)

        if rt is None or rt["revoked_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )

        if datetime.now(timezone.utc) > rt["expires_at"]:
            rt["revoked_at"] = datetime.now(timezone.utc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )

        user_id = rt["user_id"]
        user = _users.get(user_id)
        if user is None or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )

        # Rotate: revoke old token
        rt["revoked_at"] = datetime.now(timezone.utc)

        access_token = _create_access_token(user["id"], user["email"])
        new_refresh_raw = _generate_token()
        new_refresh_hash = _sha256(new_refresh_raw)
        remember = rt["remember_me"]
        refresh_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        new_expires = datetime.now(timezone.utc) + timedelta(days=refresh_days)
        now = datetime.now(timezone.utc)

        _refresh_tokens[new_refresh_hash] = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "token_hash": new_refresh_hash,
            "expires_at": new_expires,
            "revoked_at": None,
            "remember_me": remember,
            "created_at": now,
        }

        return RefreshResponse(
            accessToken=access_token,
            refreshToken=new_refresh_raw,
        )
