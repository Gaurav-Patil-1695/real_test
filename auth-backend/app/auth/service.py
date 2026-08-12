from fastapi import Response

from app.auth.schemas import LoginRequest, LoginResponse
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.exceptions import InvalidCredentialsError


class AuthService:
    def __init__(self) -> None:
        self._user_repo = UserRepository()
        self._refresh_token_repo = RefreshTokenRepository()

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self._user_repo.get_by_email(body.email)

        if user is None or not verify_password(body.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        access_token = create_access_token(subject=str(user.id))
        refresh_token_plain, refresh_token_hash = create_refresh_token()

        await self._refresh_token_repo.create(
            user_id=user.id,
            token_hash=refresh_token_hash,
            remember_me=body.rememberMe,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token_plain,
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=settings.REFRESH_TOKEN_REMEMBER_SECONDS
            if body.rememberMe
            else settings.REFRESH_TOKEN_SECONDS,
        )

        return LoginResponse(
            accessToken=access_token,
            tokenType="bearer",
            user={
                "id": str(user.id),
                "fullName": user.full_name,
                "email": user.email,
            },
        )
