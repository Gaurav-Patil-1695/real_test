from typing import Any, Dict, Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    confirmPassword: str
    acceptTerms: bool


class UserInfo(BaseModel):
    id: str
    fullName: str
    email: str


class RegisterResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserInfo


class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = None


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserInfo


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirmPassword: str


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    user: UserInfo


class LogoutRequest(BaseModel):
    refreshToken: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    refreshToken: str


class RefreshResponse(BaseModel):
    accessToken: str
    refreshToken: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail
