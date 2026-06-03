import secrets
from urllib.parse import urlencode

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.models.identity import Identity
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.services import hashing, oauth
from app.services.jwt_service import get_jwt_service


def _pk(value):
    return value.get("id") if isinstance(value, dict) else value


def _login_html(csrf: str, error: str = "") -> str:
    # `error` is only ever a fixed server-side string (never user input) — no XSS.
    err = f'<p style="color:#c00">{error}</p>' if error else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Sign in</title></head>
<body style="font-family:system-ui,sans-serif;max-width:320px;margin:80px auto">
<h2>Sign in</h2>{err}
<form method="post" action="/login">
  <input type="hidden" name="csrf" value="{csrf}">
  <p><input name="email" type="email" placeholder="Email" required style="width:100%;padding:8px;box-sizing:border-box"></p>
  <p><input name="password" type="password" placeholder="Password" required style="width:100%;padding:8px;box-sizing:border-box"></p>
  <p><button type="submit" style="width:100%;padding:9px">Sign in</button></p>
</form></body></html>"""


class SSOController:
    @staticmethod
    async def authorize(request: Request):
        client_id = request.query_params.get("client_id")
        redirect_uri = request.query_params.get("redirect_uri")
        response_type = request.query_params.get("response_type")
        state = request.query_params.get("state", "")

        client = oauth.get_client(client_id)
        if client is None:
            raise HTTPException(400, "Unknown client_id")
        if not oauth.validate_redirect_uri(client, redirect_uri):
            raise HTTPException(400, "Invalid redirect_uri")
        if response_type != "code":
            raise HTTPException(400, "Unsupported response_type (expected 'code')")

        identity_id = request.session.get("identity_id")
        if not identity_id:
            # No central session yet — stash the request and send the user to log in.
            request.session["pending_authorize"] = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": response_type,
                "state": state,
            }
            return RedirectResponse(url="/login", status_code=303)

        # Authorize only if the logged-in user is a member of this client's tenant.
        tenant = await Tenant.where("slug", client["tenant"]).first()
        if tenant is None:
            raise HTTPException(500, "Client tenant not provisioned")
        member = (
            await Membership.where("identity_id", identity_id)
            .where("tenant_id", _pk(tenant.id))
            .first()
        )
        if member is None:
            raise HTTPException(403, "User is not a member of this tenant")

        code = await oauth.create_code(identity_id, client_id, redirect_uri)
        sep = "&" if "?" in redirect_uri else "?"
        url = f"{redirect_uri}{sep}{urlencode({'code': code, 'state': state})}"
        return RedirectResponse(url=url, status_code=303)

    @staticmethod
    async def login_form(request: Request):
        csrf = secrets.token_urlsafe(16)
        request.session["csrf"] = csrf
        return HTMLResponse(_login_html(csrf))

    @staticmethod
    async def login_submit(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        csrf: str = Form(""),
    ):
        if not csrf or csrf != request.session.get("csrf"):
            new_csrf = secrets.token_urlsafe(16)
            request.session["csrf"] = new_csrf
            return HTMLResponse(_login_html(new_csrf, "Session expired, try again."), status_code=400)

        identity = await Identity.where("email", email).first()
        if identity is None or not identity.is_active or not hashing.verify(password, identity.password):
            new_csrf = secrets.token_urlsafe(16)
            request.session["csrf"] = new_csrf
            return HTMLResponse(_login_html(new_csrf, "Invalid credentials."), status_code=401)

        request.session["identity_id"] = _pk(identity.id)
        request.session.pop("csrf", None)

        pending = request.session.pop("pending_authorize", None)
        if pending:
            return RedirectResponse(url="/authorize?" + urlencode(pending), status_code=303)
        return HTMLResponse(f"<p>Signed in as {identity.email}. No pending authorization request.</p>")

    @staticmethod
    async def token(
        grant_type: str = Form(...),
        code: str = Form(...),
        redirect_uri: str = Form(...),
        client_id: str = Form(...),
        client_secret: str = Form(...),
    ):
        if grant_type != "authorization_code":
            raise HTTPException(400, "Unsupported grant_type")

        client = oauth.get_client(client_id)
        if client is None or not oauth.verify_client_secret(client, client_secret):
            raise HTTPException(401, "Invalid client credentials")

        identity_id = await oauth.consume_code(code, client_id, redirect_uri)
        if identity_id is None:
            raise HTTPException(400, "Invalid or expired code")

        identity = await Identity.find(int(identity_id))
        if identity is None:
            raise HTTPException(400, "Identity not found")

        jwt_service = get_jwt_service()
        token = jwt_service.issue(
            subject=identity_id, tenant=client["tenant"], email=identity.email
        )
        return JSONResponse(
            {"access_token": token, "token_type": "bearer", "expires_in": jwt_service.ttl}
        )

    @staticmethod
    async def logout(request: Request):
        request.session.clear()
        return JSONResponse({"message": "logged out"})
