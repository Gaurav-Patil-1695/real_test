from fastapi import APIRouter, Depends, Response, status

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
)
from app.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await service.login(body, response)
