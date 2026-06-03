from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    tenant: str = Field(..., min_length=1, description="Tenant slug, e.g. 'tenant-a'")
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyRequest(BaseModel):
    token: str = Field(..., min_length=1)
