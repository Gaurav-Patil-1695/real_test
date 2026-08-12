from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class RegisterResponse(BaseModel):
    id: int
    full_name: str = Field(..., alias="fullName")
    email: str
    created_at: str = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool | None = Field(default=None, alias="rememberMe")

    model_config = {"populate_by_name": True}


class MeResponse(BaseModel):
    id: int
    full_name: str = Field(..., alias="fullName")
    email: str
    is_active: bool = Field(..., alias="isActive")
    created_at: str = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}


class LoginResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")
    user: MeResponse

    model_config = {"populate_by_name": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class ResetPasswordResponse(BaseModel):
    message: str


class LogoutResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    access_token: str = Field(..., alias="accessToken")
    token_type: str = Field(..., alias="tokenType")

    model_config = {"populate_by_name": True}


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorDetail
