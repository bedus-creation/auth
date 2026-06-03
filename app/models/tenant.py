from fastapi_startkit.masoniteorm.models import Model


class Tenant(Model):
    __table__ = "tenants"

    slug: str
    name: str
