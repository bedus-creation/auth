from fastapi import Depends, HTTPException

from app.http.dependencies.auth import auth
from app.http.schemas.auth import LoginRequest, TokenResponse, VerifyRequest
from app.models.identity import Identity
from app.services import hashing
from app.services.jwt_service import get_jwt_service


def _pk(value):
    """masoniteorm + asyncpg can return the inserted PK as {"id": n}; normalise it."""
    return value.get("id") if isinstance(value, dict) else value


class AuthController:
    @staticmethod
    async def login(data: LoginRequest) -> TokenResponse:
        # Generic 401 on every failure so we never reveal which field was wrong.
        invalid = HTTPException(status_code=401, detail="Invalid credentials")

        identity = (
            await Identity.where("tenant", data.tenant)
            .where("email", data.email)
            .first()
        )
        if identity is None or not identity.is_active:
            raise invalid
        if not hashing.verify(data.password, identity.password):
            raise invalid

        jwt_service = get_jwt_service()
        token = jwt_service.issue(
            subject=_pk(identity.id),
            tenant=identity.tenant,
            email=identity.email,
        )
        return TokenResponse(access_token=token, expires_in=jwt_service.ttl)

    @staticmethod
    async def me(claims: dict = Depends(auth)) -> dict:
        identity = await Identity.find(int(claims["sub"]))
        if identity is None:
            raise HTTPException(status_code=404, detail="Identity not found")
        return {
            "id": _pk(identity.id),
            "tenant": identity.tenant,
            "email": identity.email,
            "name": identity.name,
            "is_active": identity.is_active,
        }

    @staticmethod
    async def verify(data: VerifyRequest) -> dict:
        try:
            claims = get_jwt_service().decode(data.token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"valid": True, "claims": claims}
