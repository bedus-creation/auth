import hmac

from fastapi import Form, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant
from config.auth import AuthConfig


def _pk(value):
    return value.get("id") if isinstance(value, dict) else value


class MembershipController:
    @staticmethod
    async def add_member(
        slug: str,
        request: Request,
        email: str = Form(...),
        role: str = Form("member"),
    ):
        """A tenant adds a (global) user to itself. Guarded by the admin secret."""
        expected = AuthConfig().admin_secret
        provided = request.headers.get("x-admin-secret", "")
        if not expected or not hmac.compare_digest(str(expected), str(provided)):
            raise HTTPException(401, "Invalid admin secret")

        tenant = await Tenant.where("slug", slug).first()
        if tenant is None:
            raise HTTPException(404, "Tenant not found")
        identity = await Identity.where("email", email).first()
        if identity is None:
            raise HTTPException(404, "User not found")

        await Membership.first_or_create(
            {"identity_id": _pk(identity.id), "tenant_id": _pk(tenant.id)},
            {"identity_id": _pk(identity.id), "tenant_id": _pk(tenant.id), "role": role},
        )
        return JSONResponse({"message": f"{email} added to {slug}", "role": role})
