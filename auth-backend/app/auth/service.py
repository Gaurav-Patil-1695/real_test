import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Response
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
PASSWORD_RESET_EXPIRE_MINUTES: int = 30


def _hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession,
) -> LoginResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None or not _verify_password(body.password, user.password_hash):
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=401,
        )

    if not user.is_active:
        raise AppError(
            code="ACCOUNT_INACTIVE",
            message="Invalid email or password.",
            status_code=401,
        )

    access_token = _create_access_token(str(user.id))
    raw_refresh = _create_refresh_token()
    refresh_hash = _hash_sha256(raw_refresh)

    remember = getattr(body, "rememberMe", False) or False
    expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
        remember_me=remember,
    )
    db.add(token_record)
    await db.commit()
    await db.refresh(token_record)

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=int(timedelta(days=expire_days).total_seconds()),
    )

    return LoginResponse(
        accessToken=access_token,
        tokenType="bearer",
    )


async def register(
    body: RegisterRequest,
    db: AsyncSession,
) -> RegisterResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    existing: Optional[User] = result.scalar_one_or_none()
    if existing is not None:
        raise AppError(
            code="EMAIL_TAKEN",
            message="An account with this email already exists.",
            status_code=409,
        )

    if body.password != body.confirmPassword:
        raise AppError(
            code="PASSWORD_MISMATCH",
            message="Passwords do not match.",
            status_code=422,
        )

    strength_error = _validate_password_strength(body.password)
    if strength_error:
        raise AppError(
            code="WEAK_PASSWORD",
            message=strength_error,
            status_code=422,
        )

    password_hash = _hash_password(body.password)
    user = User(
        full_name=body.fullName,
        email=body.email,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=str(user.id),
        fullName=user.full_name,
        email=user.email,
    )


async def forgotPassword(
    body: ForgotPasswordRequest,
    db: AsyncSession,
) -> ForgotPasswordResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user: Optional[User] = result.scalar_one_or_none()

    if user is not None and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_sha256(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

        reset_record = PasswordReset(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_record)
        await db.commit()
        # In a real system, send raw_token via email here.

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


async def resetPassword(
    body: ResetPasswordRequest,
    db: AsyncSession,
) -> ResetPasswordResponse:
    if body.password != body.confirmPassword:
        raise AppError(
            code="PASSWORD_MISMATCH",
            message="Passwords do not match.",
            status_code=422,
        )

    strength_error = _validate_password_strength(body.password)
    if strength_error:
        raise AppError(
            code="WEAK_PASSWORD",
            message=strength_error,
            status_code=422,
        )

    token_hash = _hash_sha256(body.token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token_hash == token_hash,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > now,
        )
    )
    reset_record: Optional[PasswordReset] = result.scalar_one_or_none()

    if reset_record is None:
        raise AppError(
            code="INVALID_OR_EXPIRED_TOKEN",
            message="This password reset link is invalid or has expired.",
            status_code=400,
        )

    user_result = await db.execute(select(User).where(User.id == reset_record.user_id))
    user: Optional[User] = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise AppError(
            code="INVALID_OR_EXPIRED_TOKEN",
            message="This password reset link is invalid or has expired.",
            status_code=400,
        )

    user.password_hash = _hash_password(body.password)
    user.updated_at = now
    reset_record.used_at = now

    # Revoke all existing refresh tokens for the user
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    await db.commit()

    return ResetPasswordResponse(
        message="Your password has been reset successfully. Please log in with your new password."
    )


async def me(
    current_user: User,
    db: AsyncSession,
) -> MeResponse:
    return MeResponse(
        id=str(current_user.id),
        fullName=current_user.full_name,
        email=current_user.email,
        isActive=current_user.is_active,
    )


async def logout(
    body: LogoutRequest,
    response: Response,
    current_user: User,
    db: AsyncSession,
) -> LogoutResponse:
    raw_refresh = getattr(body, "refreshToken", None)
    if raw_refresh:
        token_hash = _hash_sha256(raw_refresh)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == current_user.id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        token_record: Optional[RefreshToken] = result.scalar_one_or_none()
        if token_record:
            token_record.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    response.delete_cookie(key="refresh_token")
    return LogoutResponse(message="Logged out successfully.")


async def refresh(
    body: RefreshRequest,
    response: Response,
    db: AsyncSession,
) -> RefreshResponse:
    raw_refresh = body.refreshToken
    token_hash = _hash_sha256(raw_refresh)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    token_record: Optional[RefreshToken] = result.scalar_one_or_none()

    if token_record is None:
        raise AppError(
            code="INVALID_REFRESH_TOKEN",
            message="Refresh token is invalid or has expired.",
            status_code=401,
        )

    # Revoke old token (rotation)
    token_record.revoked_at = now

    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user: Optional[User] = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise AppError(
            code="INVALID_REFRESH_TOKEN",
            message="Refresh token is invalid or has expired.",
            status_code=401,
        )

    access_token = _create_access_token(str(user.id))
    new_raw_refresh = _create_refresh_token()
    new_refresh_hash = _hash_sha256(new_raw_refresh)

    remember = token_record.remember_me
    expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
    expires_at = now + timedelta(days=expire_days)

    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=new_refresh_hash,
        expires_at=expires_at,
        remember_me=remember,
    )
    db.add(new_token_record)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=int(timedelta(days=expire_days).total_seconds()),
    )

    return RefreshResponse(
        accessToken=access_token,
        tokenType="bearer",
    )
