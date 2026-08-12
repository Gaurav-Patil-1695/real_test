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

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))

REFRESH_COOKIE_NAME: str = "refresh_token"

# In-memory stores — replace with DB repositories in production
# Structure: keyed by id
_users: dict = {}
_password_resets: dict = {}
_refresh_tokens: dict = {}

_user_id_counter: int = 0
_pr_id_counter: int = 0
_rt_id_counter: int = 0


def _next_user_id() -> int:
    global _user_id_counter
    _user_id_counter += 1
    return _user_id_counter


def _next_pr_id() -> int:
    global _pr_id_counter
    _pr_id_counter += 1
    return _pr_id_counter


def _next_rt_id() -> int:
    global _rt_id_counter
    _rt_id_counter += 1
    return _rt_id_counter


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token_value() -> str:
    return os.urandom(32).hex()


def _set_refresh_cookie(response: Response, token_value: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400 if remember_me else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token_value,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )


def _find_user_by_email(email: str) -> Optional[dict]:
    for user in _users.values():
        if user["email"] == email:
            return user
    return None


def _find_user_by_id(user_id: int) -> Optional[dict]:
    return _users.get(user_id)


def _find_refresh_token_by_hash(token_hash: str) -> Optional[dict]:
    for rt in _refresh_tokens.values():
        if rt["token_hash"] == token_hash:
            return rt
    return None


def _validate_password_strength(password: str) -> None:
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": errors[0],
                    "details": errors,
                }
            },
        )


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired.",
                    "details": [],
                }
            },
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid token.",
                    "details": [],
                }
            },
        )


def _extract_bearer_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


class AuthService:
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": [],
                    }
                },
            )

        _validate_password_strength(body.password)

        if _find_user_by_email(body.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": [],
                    }
                },
            )

        user_id = _next_user_id()
        now = datetime.now(timezone.utc)
        user = {
            "id": user_id,
            "full_name": body.full_name,
            "email": body.email,
            "password_hash": _hash_password(body.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        _users[user_id] = user

        return RegisterResponse(
            id=user_id,
            fullName=user["full_name"],
            email=user["email"],
            createdAt=user["created_at"].isoformat(),
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = _find_user_by_email(body.email)
        if not user or not _verify_password(body.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": [],
                    }
                },
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "Account is inactive.",
                        "details": [],
                    }
                },
            )

        access_token = _create_access_token(user["id"], user["email"])
        refresh_token_value = _create_refresh_token_value()
        remember_me: bool = body.remember_me if body.remember_me is not None else False
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expire_days)

        rt_id = _next_rt_id()
        _refresh_tokens[rt_id] = {
            "id": rt_id,
            "user_id": user["id"],
            "token_hash": _sha256(refresh_token_value),
            "expires_at": expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }

        _set_refresh_cookie(response, refresh_token_value, remember_me)

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
            user=MeResponse(
                id=user["id"],
                fullName=user["full_name"],
                email=user["email"],
                isActive=user["is_active"],
                createdAt=user["created_at"].isoformat(),
            ),
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = _find_user_by_email(body.email)
        if user:
            raw_token = os.urandom(32).hex()
            token_hash = _sha256(raw_token)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=1)
            pr_id = _next_pr_id()
            _password_resets[pr_id] = {
                "id": pr_id,
                "user_id": user["id"],
                "token_hash": token_hash,
                "expires_at": expires_at,
                "used_at": None,
                "created_at": now,
            }
            # In production: send email with raw_token

        return ForgotPasswordResponse(
            message="If that email is registered, you will receive a password reset link shortly."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "PASSWORD_MISMATCH",
                        "message": "Passwords do not match.",
                        "details": [],
                    }
                },
            )

        _validate_password_strength(body.password)

        token_hash = _sha256(body.token)
        now = datetime.now(timezone.utc)

        pr_record = None
        for pr in _password_resets.values():
            if (
                pr["token_hash"] == token_hash
                and pr["used_at"] is None
                and pr["expires_at"] > now
            ):
                pr_record = pr
                break

        if not pr_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_OR_EXPIRED_TOKEN",
                        "message": "This reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        user = _find_user_by_id(pr_record["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_OR_EXPIRED_TOKEN",
                        "message": "This reset link is invalid or has expired.",
                        "details": [],
                    }
                },
            )

        user["password_hash"] = _hash_password(body.password)
        user["updated_at"] = now
        pr_record["used_at"] = now

        # Revoke all refresh tokens for this user
        for rt in _refresh_tokens.values():
            if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
                rt["revoked_at"] = now

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    async def me(self, request: Request) -> MeResponse:
        token = _extract_bearer_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_TOKEN",
                        "message": "Authentication token is required.",
                        "details": [],
                    }
                },
            )

        payload = _decode_access_token(token)
        user_id = int(payload["sub"])
        user = _find_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "User not found.",
                        "details": [],
                    }
                },
            )

        return MeResponse(
            id=user["id"],
            fullName=user["full_name"],
            email=user["email"],
            isActive=user["is_active"],
            createdAt=user["created_at"].isoformat(),
        )

    async def logout(
        self, request: Request, response: Response
    ) -> LogoutResponse:
        token = _extract_bearer_token(request)
        if token:
            try:
                payload = _decode_access_token(token)
                user_id = int(payload["sub"])
                now = datetime.now(timezone.utc)
                for rt in _refresh_tokens.values():
                    if rt["user_id"] == user_id and rt["revoked_at"] is None:
                        rt["revoked_at"] = now
            except HTTPException:
                pass

        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self,
        request: Request,
        response: Response,
        refresh_token: Optional[str],
    ) -> RefreshResponse:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_REFRESH_TOKEN",
                        "message": "Refresh token is required.",
                        "details": [],
                    }
                },
            )

        token_hash = _sha256(refresh_token)
        now = datetime.now(timezone.utc)

        rt_record = _find_refresh_token_by_hash(token_hash)

        if not rt_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_REFRESH_TOKEN",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    }
                },
            )

        if rt_record["revoked_at"] is not None:
            # Token reuse detected — revoke all tokens for this user
            user_id_compromised = rt_record["user_id"]
            for rt in _refresh_tokens.values():
                if rt["user_id"] == user_id_compromised and rt["revoked_at"] is None:
                    rt["revoked_at"] = now
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_REUSE",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    }
                },
            )

        if rt_record["expires_at"] <= now:
            rt_record["revoked_at"] = now
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "REFRESH_TOKEN_EXPIRED",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    }
                },
            )

        user = _find_user_by_id(rt_record["user_id"])
        if not user or not user["is_active"]:
            rt_record["revoked_at"] = now
            _clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "USER_NOT_FOUND",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    }
                },
            )

        # Rotate: revoke old token
        rt_record["revoked_at"] = now

        # Issue new refresh token
        new_refresh_token_value = _create_refresh_token_value()
        remember_me: bool = rt_record["remember_me"]
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
        new_expires_at = now + timedelta(days=expire_days)

        new_rt_id = _next_rt_id()
        _refresh_tokens[new_rt_id] = {
            "id": new_rt_id,
            "user_id": user["id"],
            "token_hash": _sha256(new_refresh_token_value),
            "expires_at": new_expires_at,
            "revoked_at": None,
            "remember_me": remember_me,
            "created_at": now,
        }

        new_access_token = _create_access_token(user["id"], user["email"])
        _set_refresh_cookie(response, new_refresh_token_value, remember_me)

        return RefreshResponse(
            accessToken=new_access_token,
            tokenType="bearer",
        )
