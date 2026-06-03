from dataclasses import field

from fastapi_startkit.environment import env
from pydantic.dataclasses import dataclass


@dataclass
class AuthConfig:
    """JWT settings for issuing and verifying access tokens (HS256)."""

    jwt_secret: str = field(default_factory=lambda: env("JWT_SECRET", "change-me"))
    jwt_algorithm: str = field(default_factory=lambda: env("JWT_ALGORITHM", "HS256"))
    jwt_ttl: int = field(default_factory=lambda: int(env("JWT_TTL", "3600")))
