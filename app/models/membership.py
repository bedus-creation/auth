from fastapi_startkit.masoniteorm.models import Model


class Membership(Model):
    """Pivot linking a global Identity to a Tenant it may access."""

    __table__ = "identity_tenant"

    identity_id: int
    tenant_id: int
    role: str
