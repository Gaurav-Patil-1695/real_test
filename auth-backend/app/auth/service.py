from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Response

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.auth.repository import AuthRepository
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
    generate_token,
)
from app.models.user import User
from fastapi import HTTPException, status


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self.repository.get_user_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Invalid email or password.",
                    "details": {},
                },
            )

        access_token = create_access_token({"sub": str(user.id)})
        raw_refresh_token = generate_token()
        token_hash = hash_token(raw_refresh_token)
        remember_me = body.remember_me if body.remember_me is not None else False
        expires_at = datetime.now(timezone.utc) + (
            timedelta(days=settings.REFRESH_TOKEN_REMEMBER_DAYS)
            if remember_me
            else timedelta(days=settings.REFRESH_TOKEN_DAYS)
        )
        await self.repository.create_refresh_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            expires=int(expires_at.timestamp()),
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        existing = await self.repository.get_user_by_email(body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": {"field": "email"},
                },
            )

        password_hash = hash_password(body.password)
        user = await self.repository.create_user(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )

        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = await self.repository.get_user_by_email(body.email)
        if user is not None and user.is_active:
            raw_token = generate_token()
            token_hash = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
            )
            await self.repository.create_password_reset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # In a real system, send email with raw_token here.

        return ForgotPasswordResponse(
            message="If that email address is in our system, we emailed you a link to reset your password."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = hash_token(body.token)
        reset_record = await self.repository.get_valid_password_reset(token_hash)
        if reset_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": {},
                },
            )

        new_hash = hash_password(body.password)
        await self.repository.update_user_password(reset_record.user_id, new_hash)
        await self.repository.mark_password_reset_used(reset_record.id)
        await self.repository.revoke_all_refresh_tokens(reset_record.user_id)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, current_user: User) -> MeResponse:
        return MeResponse(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )

    async def logout(self, body: LogoutRequest, response: Response) -> LogoutResponse:
        if body.refresh_token:
            token_hash = hash_token(body.refresh_token)
            await self.repository.revoke_refresh_token_by_hash(token_hash)

        response.delete_cookie(key="refresh_token")

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(self, body: RefreshRequest, response: Response) -> RefreshResponse:
        raw_token = body.refresh_token
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "MISSING_REFRESH_TOKEN",
                    "message": "Refresh token is required.",
                    "details": {},
                },
            )

        token_hash = hash_token(raw_token)
        stored = await self.repository.get_valid_refresh_token(token_hash)
        if stored is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        await self.repository.revoke_refresh_token_by_hash(token_hash)

        user = await self.repository.get_user_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has expired.",
                    "details": {},
                },
            )

        access_token = create_access_token({"sub": str(user.id)})
        new_raw_refresh = generate_token()
        new_hash = hash_token(new_raw_refresh)
        remember_me = stored.remember_me
        expires_at = datetime.now(timezone.utc) + (
            timedelta(days=settings.REFRESH_TOKEN_REMEMBER_DAYS)
            if remember_me
            else timedelta(days=settings.REFRESH_TOKEN_DAYS)
        )
        await self.repository.create_refresh_token(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_raw_refresh,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            expires=int(expires_at.timestamp()),
        )

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )
