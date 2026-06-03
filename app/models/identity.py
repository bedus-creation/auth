from typing import TYPE_CHECKING, Optional

from fastapi_startkit.masoniteorm.models import Model
from fastapi_startkit.masoniteorm.relationships import BelongsTo

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Identity(Model):
    __table__ = "identity"
    __hidden__ = ["password"]

    tenant_id: int
    email: str
    password: Optional[str]
    name: Optional[str]
    is_active: bool

    tenant = BelongsTo("Tenant")
