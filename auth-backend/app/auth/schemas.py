from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    password: str
    confirmPassword: str


class UserInfo(BaseModel):
    id: int
    fullName: str
    email: str


class RegisterResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserInfo


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = None


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserInfo


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirmPassword: str


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: int
    fullName: str
    email: str


class LogoutRequest(BaseModel):
    refreshToken: Optional[str] = None


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
