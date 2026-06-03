from fastapi import Depends, HTTPException

from app.http.dependencies.auth import auth
from app.http.schemas.auth import LoginRequest, TokenResponse, VerifyRequest
from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.services import hashing
from app.services.jwt_service import get_jwt_service


def _pk(value):
    """masoniteorm + asyncpg can return the inserted PK as {"id": n}; normalise it."""
    return value.get("id") if isinstance(value, dict) else value


class AuthController:
    @staticmethod
    async def login(data: LoginRequest) -> TokenResponse:
        """Direct JSON login for API/SPA clients. Verifies the global identity and
        that it is a member of the requested tenant, then issues a JWT for it."""
        invalid = HTTPException(status_code=401, detail="Invalid credentials")

        identity = await Identity.where("email", data.email).first()
        if identity is None or not identity.is_active:
            raise invalid
        if not hashing.verify(data.password, identity.password):
            raise invalid

        tenant = await Tenant.where("slug", data.tenant).first()
        if tenant is None:
            raise invalid
        member = (
            await Membership.where("identity_id", _pk(identity.id))
            .where("tenant_id", _pk(tenant.id))
            .first()
        )
        if member is None:
            raise HTTPException(status_code=403, detail="User is not a member of this tenant")

        jwt_service = get_jwt_service()
        token = jwt_service.issue(
            subject=_pk(identity.id), tenant=tenant.slug, email=identity.email
        )
        return TokenResponse(access_token=token, expires_in=jwt_service.ttl)

    @staticmethod
    async def me(claims: dict = Depends(auth)) -> dict:
        identity = await Identity.find(int(claims["sub"]))
        if identity is None:
            raise HTTPException(status_code=404, detail="Identity not found")

        memberships = await Membership.where("identity_id", _pk(identity.id)).get()
        tenant_ids = [m.tenant_id for m in memberships]
        slugs = []
        if tenant_ids:
            tenants = await Tenant.where_in("id", tenant_ids).get()
            slugs = [t.slug for t in tenants]

        return {
            "id": _pk(identity.id),
            "email": identity.email,
            "name": identity.name,
            "is_active": identity.is_active,
            "tenants": slugs,
        }

    @staticmethod
    async def verify(data: VerifyRequest) -> dict:
        try:
            claims = get_jwt_service().decode(data.token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"valid": True, "claims": claims}
