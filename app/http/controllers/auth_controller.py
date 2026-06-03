from fastapi import Depends, HTTPException

from app.http.dependencies.auth import auth
from app.http.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, VerifyRequest
from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.services import hashing
from app.services import refresh_service
from app.services.jwt_service import get_jwt_service


def _pk(value):
    return value.get("id") if isinstance(value, dict) else value


async def _issue_tokens(identity_id: int, tenant_slug: str, email: str) -> TokenResponse:
    jwt_service = get_jwt_service()
    access_token = jwt_service.issue(subject=identity_id, tenant=tenant_slug, email=email)
    refresh_token = await refresh_service.create(identity_id, tenant_slug)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=jwt_service.ttl,
    )


class AuthController:

    @staticmethod
    async def login(data: LoginRequest) -> TokenResponse:
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

        return await _issue_tokens(_pk(identity.id), tenant.slug, identity.email)

    @staticmethod
    async def refresh(data: RefreshRequest) -> TokenResponse:
        """Exchange a refresh token for a new access token + new refresh token
        (rotation: old token is revoked, new one issued)."""
        row = await refresh_service.consume(data.refresh_token)
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        identity = await Identity.find(int(row.identity_id))
        if identity is None or not identity.is_active:
            raise HTTPException(status_code=401, detail="Identity not found or inactive")

        # Rotate: revoke the used token, issue a fresh pair.
        await refresh_service.revoke(data.refresh_token)
        return await _issue_tokens(int(row.identity_id), row.tenant, identity.email)

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
