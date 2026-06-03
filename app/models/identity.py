from typing import Optional

from fastapi_startkit.masoniteorm.models import Model


class Identity(Model):
    __table__ = "identity"
    __hidden__ = ["password"]

    tenant: str
    email: str
    password: Optional[str]
    name: Optional[str]
    is_active: bool
