from fastapi import Depends
from fastapi_startkit.fastapi import Router

from app.http.controllers.auth_controller import AuthController
from app.http.controllers.membership_controller import MembershipController
from app.http.controllers.sso_controller import SSOController
from app.http.dependencies.auth import auth

# Public endpoints — no access token required.
public = Router()

# Direct JSON API (non-browser clients).
public.post("/auth/login", AuthController.login)
public.post("/auth/verify", AuthController.verify)

# OAuth2 Authorization-Code SSO (browser-facing + back-channel token exchange).
public.get("/authorize", SSOController.authorize)
public.get("/login", SSOController.login_form)
public.post("/login", SSOController.login_submit)
public.post("/token", SSOController.token)
public.get("/logout", SSOController.logout)

# Tenant membership management (admin-secret guarded).
public.post("/tenants/{slug}/members", MembershipController.add_member)

# Protected endpoints — require a valid Bearer token.
protected = Router(dependencies=[Depends(auth)])
protected.get("/auth/me", AuthController.me)
