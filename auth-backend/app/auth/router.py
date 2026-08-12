from fastapi import APIRouter, Depends, Response, status
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
from app.auth.service import AuthService
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="register",
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await service.register(payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await service.login(payload)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="forgotPassword",
)
async def forgotPassword(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    return await service.forgotPassword(payload)


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    operation_id="resetPassword",
)
async def resetPassword(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ResetPasswordResponse:
    return await service.resetPassword(payload)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    operation_id="me",
)
async def me(
    service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    return await service.me()


@router.post(
    "/logout",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="logout",
)
async def logout(
    payload: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    await service.logout(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    operation_id="refresh",
)
async def refresh(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    return await service.refresh(payload)
