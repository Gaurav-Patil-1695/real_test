import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.config import settings
from app.models import PasswordReset, RefreshToken, User

import bcrypt
import jwt


FORGOT_PASSWORD_RESPONSE_MESSAGE = (
    "If that email address is in our system, we emailed you a link to reset your password."
)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": {},
                    }
                },
            )
        password_hash = _hash_password(payload.password)
        user = User(
            full_name=payload.fullName,
            email=payload.email,
            password_hash=password_hash,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        access_token = _create_access_token(user.id)
        raw_refresh = secrets.token_urlsafe(64)
        refresh_hash = _hash_token(raw_refresh)
        refresh_expires = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
            remember_me=False,
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()
        return RegisterResponse(
            accessToken=access_token,
            refreshToken=raw_refresh,
            user={
                "id": user.id,
                "fullName": user.full_name,
                "email": user.email,
            },
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        from fastapi import HTTPException, status

        result = await self.db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if user is None or not _verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": {},
                    }
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "Invalid email or password.",
                        "details": {},
                    }
                },
            )
        access_token = _create_access_token(user.id)
        raw_refresh = secrets.token_urlsafe(64)
        refresh_hash = _hash_token(raw_refresh)
        remember = payload.rememberMe if payload.rememberMe is not None else False
        days = (
            settings.refresh_token_remember_days
            if remember
            else settings.refresh_token_expire_days
        )
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=days)
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
            remember_me=remember,
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()
        return LoginResponse(
            accessToken=access_token,
            refreshToken=raw_refresh,
            user={
                "id": user.id,
                "fullName": user.full_name,
                "email": user.email,
            },
        )

    async def forgotPassword(self, payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(64)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.password_reset_expire_minutes
            )
            reset_record = PasswordReset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            self.db.add(reset_record)
            await self.db.commit()
            # In a real system, send raw_token via email here.
            # Email sending is outside the scope of this work item.

        return ForgotPasswordResponse(message=FORGOT_PASSWORD_RESPONSE_MESSAGE)

    async def resetPassword(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        from fastapi import HTTPException, status

        token_hash = _hash_token(payload.token)
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
        )
        reset_record = result.scalar_one_or_none()
        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )
        user_result = await self.db.execute(
            select(User).where(User.id == reset_record.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": {},
                    }
                },
            )
        user.password_hash = _hash_password(payload.password)
        reset_record.used_at = now
        await self.db.commit()
        return ResetPasswordResponse(message="Your password has been reset successfully. You can now log in with your new password.")

    async def me(self) -> MeResponse:
        # Placeholder — real implementation requires auth middleware injecting current user.
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "NOT_AUTHENTICATED",
                    "message": "Authentication required.",
                    "details": {},
                }
            },
        )

    async def logout(self, payload: LogoutRequest) -> None:
        if payload.refreshToken:
            token_hash = _hash_token(payload.refreshToken)
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            token_obj = result.scalar_one_or_none()
            if token_obj is not None:
                token_obj.revoked_at = datetime.now(timezone.utc)
                await self.db.commit()

    async def refresh(self, payload: RefreshRequest) -> RefreshResponse:
        from fastapi import HTTPException, status

        token_hash = _hash_token(payload.refreshToken)
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        token_obj = result.scalar_one_or_none()
        if token_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )
        token_obj.revoked_at = now
        user_result = await self.db.execute(
            select(User).where(User.id == token_obj.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Invalid or expired refresh token.",
                        "details": {},
                    }
                },
            )
        new_access_token = _create_access_token(user.id)
        raw_refresh = secrets.token_urlsafe(64)
        new_refresh_hash = _hash_token(raw_refresh)
        remember = token_obj.remember_me if token_obj.remember_me is not None else False
        days = (
            settings.refresh_token_remember_days
            if remember
            else settings.refresh_token_expire_days
        )
        new_expires = now + timedelta(days=days)
        new_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=new_expires,
            remember_me=remember,
        )
        self.db.add(new_token_obj)
        await self.db.commit()
        return RefreshResponse(
            accessToken=new_access_token,
            refreshToken=raw_refresh,
        )
