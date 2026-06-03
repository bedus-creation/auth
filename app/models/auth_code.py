from typing import Optional

from fastapi_startkit.masoniteorm.models import Model


class AuthCode(Model):
    """A one-time OAuth2 authorization code. `expires_at` is epoch seconds."""

    __table__ = "auth_codes"

    code: str
    identity_id: int
    client_id: str
    redirect_uri: str
    expires_at: int
    used: bool
