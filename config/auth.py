from dataclasses import field

from fastapi_startkit.environment import env
from pydantic.dataclasses import dataclass


@dataclass
class AuthConfig:
    """JWT + central session settings."""

    jwt_secret: str = field(default_factory=lambda: env("JWT_SECRET", "change-me"))
    jwt_algorithm: str = field(default_factory=lambda: env("JWT_ALGORITHM", "HS256"))
    jwt_ttl: int = field(default_factory=lambda: int(env("JWT_TTL", "3600")))

    # Signs the central session cookie (idp_session).
    session_secret: str = field(
        default_factory=lambda: env("SESSION_SECRET", "dev-session-secret-change-me-min-32-bytes")
    )

    # Admin secret for tenant membership management.
    admin_secret: str = field(default_factory=lambda: env("ADMIN_SECRET", "dev-admin-secret"))
