from typing import Optional

from fastapi_startkit.masoniteorm.models import Model


class Identity(Model):
    """A global user. Email is unique across the whole system; tenant access is
    granted via the `identity_tenant` membership table (see Membership)."""

    __table__ = "identity"
    __hidden__ = ["password"]

    email: str
    password: Optional[str]
    name: Optional[str]
    is_active: bool
