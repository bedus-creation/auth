"""Simple centralized SSO.

Flow:
  1. Tenant has no session → redirect to:
       GET /sso?tenant=tenant-a&redirect=http://tenant-a.com/auth/callback
  2. Auth checks central session (idp_session cookie):
       - No session  → show login page
       - Has session → check membership → redirect back with ?token=<JWT>
  3. POST /login   → verify credentials → set session → back to /sso
  4. GET  /logout  → clear session

No client_id, no client_secret, no state, no code exchange. The JWT is returned
directly in the redirect so the tenant just reads ?token= and stores it.
"""

import secrets
from urllib.parse import urlencode

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.services import hashing, refresh_service
from app.services.jwt_service import get_jwt_service


def _pk(v):
    return v.get("id") if isinstance(v, dict) else v


def _login_page(csrf: str, error: str = "", redirect_back: str = "") -> str:
    err = f'<p style="color:#c00;margin:0 0 12px">{error}</p>' if error else ""
    hidden = f'<input type="hidden" name="redirect_back" value="{redirect_back}">' if redirect_back else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Sign in</title>
<style>body{{font-family:system-ui,sans-serif;max-width:340px;margin:80px auto;padding:0 16px}}
input{{width:100%;padding:9px;box-sizing:border-box;margin-bottom:10px;border:1px solid #ccc;border-radius:4px}}
button{{width:100%;padding:10px;background:#111;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:15px}}</style>
</head><body>
<h2 style="margin-bottom:20px">Sign in</h2>{err}
<form method="post" action="/login">
  <input type="hidden" name="csrf" value="{csrf}">{hidden}
  <input name="email" type="email" placeholder="Email" required value="multi@example.com">
  <input name="password" type="password" placeholder="Password" required value="secret">
  <button type="submit">Sign in</button>
</form></body></html>"""


class SSOController:

    @staticmethod
    async def sso(request: Request):
        """Entry point tenants redirect to. Returns a JWT in the redirect on success."""
        # Normalise tenant_a -> tenant-a so either convention works.
        tenant_slug = request.query_params.get("tenant", "").replace("_", "-")
        redirect_uri = request.query_params.get("redirect", "")

        if not tenant_slug or not redirect_uri:
            return RedirectResponse(url="/login", status_code=303)

        identity_id = request.session.get("identity_id")

        if not identity_id:
            # No central session — stash where to go and send to login.
            request.session["sso_pending"] = {"tenant": tenant_slug, "redirect": redirect_uri}
            return RedirectResponse(url="/login", status_code=303)

        return await SSOController._issue_and_redirect(identity_id, tenant_slug, redirect_uri)

    @staticmethod
    async def _issue_and_redirect(identity_id: int, tenant_slug: str, redirect_uri: str):
        print(f"[SSO] _issue_and_redirect identity_id={identity_id} tenant={tenant_slug} redirect={redirect_uri}", flush=True)

        tenant = await Tenant.where("slug", tenant_slug).first()
        if tenant is None:
            print(f"[SSO] FAIL: tenant '{tenant_slug}' not found", flush=True)
            return RedirectResponse(url="/login", status_code=303)

        member = (
            await Membership.where("identity_id", identity_id)
            .where("tenant_id", _pk(tenant.id))
            .first()
        )
        if member is None:
            print(f"[SSO] FAIL: identity {identity_id} not a member of tenant {tenant_slug} (tenant_id={_pk(tenant.id)})", flush=True)
            return RedirectResponse(url="/login", status_code=303)

        identity = await Identity.find(int(identity_id))
        if identity is None or not identity.is_active:
            print(f"[SSO] FAIL: identity {identity_id} not found or inactive", flush=True)
            return RedirectResponse(url="/login", status_code=303)

        jwt_service = get_jwt_service()
        access_token = jwt_service.issue(
            subject=identity_id, tenant=tenant_slug, email=identity.email
        )
        refresh_token = await refresh_service.create(identity_id, tenant_slug)

        sep = "&" if "?" in redirect_uri else "?"
        params = {"token": access_token, "refresh_token": refresh_token}
        return RedirectResponse(url=f"{redirect_uri}{sep}{urlencode(params)}", status_code=303)

    @staticmethod
    async def login_form(request: Request):
        csrf = secrets.token_urlsafe(16)
        request.session["csrf"] = csrf
        pending = request.session.get("sso_pending", {})
        redirect_back = f"/sso?{urlencode(pending)}" if pending else ""
        return HTMLResponse(_login_page(csrf, redirect_back=redirect_back))

    @staticmethod
    async def login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        csrf: str = Form(""),
        redirect_back: str = Form(""),
    ):
        if not csrf or csrf != request.session.get("csrf"):
            return RedirectResponse(url="/login", status_code=303)

        identity = await Identity.where("email", email).first()
        if identity is None or not identity.is_active or not hashing.verify(password, identity.password):
            new_csrf = secrets.token_urlsafe(16)
            request.session["csrf"] = new_csrf
            return HTMLResponse(_login_page(new_csrf, "Invalid credentials.", redirect_back), status_code=401)

        request.session["identity_id"] = _pk(identity.id)
        request.session.pop("csrf", None)

        # Resume the pending SSO request if there was one.
        pending = request.session.pop("sso_pending", None)
        if pending:
            return RedirectResponse(url=f"/sso?{urlencode(pending)}", status_code=303)
        if redirect_back:
            return RedirectResponse(url=redirect_back, status_code=303)

        return JSONResponse({"message": f"Signed in as {identity.email}"})

    @staticmethod
    async def logout(request: Request):
        redirect_to = request.query_params.get("redirect", "")
        request.session.clear()
        if redirect_to:
            return RedirectResponse(url=redirect_to, status_code=303)
        return JSONResponse({"message": "Signed out"})
