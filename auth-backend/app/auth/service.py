import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.db import get_connection

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS = int(os.getenv("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))
REFRESH_COOKIE_NAME = "refresh_token"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_refresh_token() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Token has expired.", "details": []},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Invalid token.", "details": []},
        )


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400 if remember_me else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/auth/refresh",
    )


class AuthService:
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": [],
                },
            )
        async with get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", body.email
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": [],
                    },
                )
            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()
            row = await conn.fetchrow(
                """
                INSERT INTO users (full_name, email, password_hash, is_active)
                VALUES ($1, $2, $3, TRUE)
                RETURNING id, full_name, email, created_at
                """,
                body.full_name,
                body.email,
                password_hash,
            )
        return RegisterResponse(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            created_at=row["created_at"],
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "details": [],
            },
        )
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, password_hash, is_active FROM users WHERE email = $1",
                body.email,
            )
            if not row:
                raise invalid_exc
            if not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
                raise invalid_exc
            if not row["is_active"]:
                raise invalid_exc

            access_token = _make_access_token(row["id"], row["email"])
            raw_refresh = _make_refresh_token()
            token_hash = _hash_token(raw_refresh)
            remember_me = body.remember_me if body.remember_me is not None else False
            expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                row["id"],
                token_hash,
                expires_at,
                remember_me,
            )

        _set_refresh_cookie(response, raw_refresh, remember_me)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 AND is_active = TRUE", body.email
            )
            if row:
                raw_token = _make_refresh_token()
                token_hash = _hash_token(raw_token)
                expires_at = datetime.now(timezone.utc) + timedelta(
                    minutes=PASSWORD_RESET_EXPIRE_MINUTES
                )
                await conn.execute(
                    """
                    INSERT INTO password_resets (user_id, token_hash, expires_at)
                    VALUES ($1, $2, $3)
                    """,
                    row["id"],
                    token_hash,
                    expires_at,
                )
                # In a real system the reset link would be emailed here.
        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "PASSWORD_MISMATCH",
                    "message": "Passwords do not match.",
                    "details": [],
                },
            )
        token_hash = _hash_token(body.token)
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, expires_at, used_at
                FROM password_resets
                WHERE token_hash = $1
                """,
                token_hash,
            )
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_RESET_TOKEN",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    },
                )
            if row["used_at"] is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "RESET_TOKEN_USED",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    },
                )
            if row["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "RESET_TOKEN_EXPIRED",
                        "message": "This password reset link is invalid or has expired.",
                        "details": [],
                    },
                )
            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()
            await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2",
                password_hash,
                row["user_id"],
            )
            await conn.execute(
                "UPDATE password_resets SET used_at = NOW() WHERE id = $1",
                row["id"],
            )
            # Revoke all refresh tokens for this user.
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = $1 AND revoked_at IS NULL",
                row["user_id"],
            )
        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, token: str) -> MeResponse:
        payload = _decode_access_token(token)
        user_id = int(payload["sub"])
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, is_active, created_at, updated_at FROM users WHERE id = $1",
                user_id,
            )
        if not row or not row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "USER_NOT_FOUND", "message": "User not found.", "details": []},
            )
        return MeResponse(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def logout(self, token: str, request: Request, response: Response) -> LogoutResponse:
        payload = _decode_access_token(token)
        user_id = int(payload["sub"])

        raw_refresh: Optional[str] = request.cookies.get(REFRESH_COOKIE_NAME)

        async with get_connection() as conn:
            if raw_refresh:
                token_hash = _hash_token(raw_refresh)
                await conn.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = NOW()
                    WHERE token_hash = $1
                      AND user_id = $2
                      AND revoked_at IS NULL
                    """,
                    token_hash,
                    user_id,
                )
            else:
                # Revoke all active refresh tokens for the user when no specific cookie is present.
                await conn.execute(
                    """
                    UPDATE refresh_tokens
                    SET revoked_at = NOW()
                    WHERE user_id = $1
                      AND revoked_at IS NULL
                    """,
                    user_id,
                )

        _clear_refresh_cookie(response)
        return LogoutResponse(message="You have been logged out successfully.")

    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        raw_refresh: Optional[str] = request.cookies.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "MISSING_REFRESH_TOKEN",
                    "message": "Refresh token is missing.",
                    "details": [],
                },
            )
        token_hash = _hash_token(raw_refresh)
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked_at, rt.remember_me,
                       u.email, u.is_active
                FROM refresh_tokens rt
                JOIN users u ON u.id = rt.user_id
                WHERE rt.token_hash = $1
                """,
                token_hash,
            )
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    },
                )
            if row["revoked_at"] is not None:
                # Token reuse detected — revoke all tokens for the user.
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = $1 AND revoked_at IS NULL",
                    row["user_id"],
                )
                _clear_refresh_cookie(response)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "REFRESH_TOKEN_REUSE",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    },
                )
            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "REFRESH_TOKEN_EXPIRED",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    },
                )
            if not row["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "USER_INACTIVE",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    },
                )
            # Rotate: revoke old token.
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = $1",
                row["id"],
            )
            # Issue new refresh token.
            new_raw_refresh = _make_refresh_token()
            new_token_hash = _hash_token(new_raw_refresh)
            remember_me = row["remember_me"]
            expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                row["user_id"],
                new_token_hash,
                new_expires_at,
                remember_me,
            )

        access_token = _make_access_token(row["user_id"], row["email"])
        _set_refresh_cookie(response, new_raw_refresh, remember_me)
        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )
