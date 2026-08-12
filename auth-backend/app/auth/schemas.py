from pydantic import BaseModel, EmailStr
from typing import Any, Dict


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: bool = False


class UserInfo(BaseModel):
    id: str
    fullName: str
    email: str


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str
    user: UserInfo

    model_config = {"populate_by_name": True}
