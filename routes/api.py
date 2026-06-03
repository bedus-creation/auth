from fastapi import Depends
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
public.get("/login", SSOController.login_form)
public.post("/login", SSOController.login_submit)
public.get("/logout", SSOController.logout)

# Protected — require a valid Bearer token.
protected = Router(dependencies=[Depends(auth)])
protected.get("/auth/me", AuthController.me)
