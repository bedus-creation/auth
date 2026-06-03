from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    tenant: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int        # access token TTL (seconds)
    refresh_expires_in: int = 60 * 60 * 24 * 30  # 30 days


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class VerifyRequest(BaseModel):
    token: str = Field(..., min_length=1)
