from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi_startkit.fastapi import Router

from app.http.controllers.auth_controller import AuthController
from app.http.controllers.sso_controller import SSOController
from app.http.dependencies.auth import auth

# Public — no token required.
public = Router()
public.post("/auth/login", AuthController.login)
public.post("/auth/refresh", AuthController.refresh)
public.post("/auth/verify", AuthController.verify)
public.get("/sso", SSOController.sso)

async def debug_session(request: Request):
    return JSONResponse({
        "session": dict(request.session),
        "cookies": dict(request.cookies),
    })
public.get("/debug/session", debug_session)
public.get("/login", SSOController.login_form)
public.post("/login", SSOController.login_submit)
public.get("/logout", SSOController.logout)

# Protected — require a valid Bearer token.
protected = Router(dependencies=[Depends(auth)])
protected.get("/auth/me", AuthController.me)
