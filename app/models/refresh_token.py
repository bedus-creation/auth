from fastapi_startkit.masoniteorm.models import Model


class RefreshToken(Model):
    __table__ = "refresh_tokens"

    token: str
    identity_id: int
    tenant: str
    expires_at: int
    revoked: bool
