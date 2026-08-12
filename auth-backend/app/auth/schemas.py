from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = False


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str


class RegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    password: str
    confirmPassword: str


class RegisterResponse(BaseModel):
    id: str
    fullName: str
    email: str


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
    id: str
    fullName: str
    email: str
    isActive: bool


class LogoutRequest(BaseModel):
    refreshToken: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    refreshToken: str


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
