from dataclasses import field

from fastapi_startkit.environment import env
from pydantic.dataclasses import dataclass


def _csv(value: str) -> list[str]:
    return [v.strip() for v in str(value).split(",") if v.strip()]


@dataclass
class AuthConfig:
    """JWT + OAuth2 SSO settings."""

    # --- JWT (access tokens, HS256) ---
    jwt_secret: str = field(default_factory=lambda: env("JWT_SECRET", "change-me"))
    jwt_algorithm: str = field(default_factory=lambda: env("JWT_ALGORITHM", "HS256"))
    jwt_ttl: int = field(default_factory=lambda: int(env("JWT_TTL", "3600")))

    # --- Central session (signed cookie) ---
    session_secret: str = field(
        default_factory=lambda: env("SESSION_SECRET", "dev-session-secret-change-me-min-32-bytes")
    )

    # --- OAuth2 authorization codes ---
    auth_code_ttl: int = field(default_factory=lambda: int(env("AUTH_CODE_TTL", "60")))

    # --- Admin secret guarding tenant membership management ---
    admin_secret: str = field(default_factory=lambda: env("ADMIN_SECRET", "dev-admin-secret"))

    # --- OAuth client registry: client_id -> {tenant slug, redirect_uris, secret} ---
    clients: dict = field(default_factory=lambda: {
        "tenant_a": {
            "tenant": "tenant-a",
            "redirect_uris": _csv(env("TENANT_A_REDIRECT_URIS", "http://localhost/auth/callback")),
            "secret": env("TENANT_A_CLIENT_SECRET", "tenant-a-client-secret"),
        },
        "tenant_b": {
            "tenant": "tenant-b",
            "redirect_uris": _csv(env("TENANT_B_REDIRECT_URIS", "http://localhost/auth/callback")),
            "secret": env("TENANT_B_CLIENT_SECRET", "tenant-b-client-secret"),
        },
    })
