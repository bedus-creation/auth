from fastapi_startkit.providers import Provider

from app.services.jwt_service import JwtService
from config.auth import AuthConfig


class AuthProvider(Provider):
    """Binds the JWT service so it can be resolved from the container as "jwt"."""

    def register(self) -> None:
        config = AuthConfig()
        self.app.bind("jwt", JwtService(
            secret=config.jwt_secret,
            algorithm=config.jwt_algorithm,
            ttl=config.jwt_ttl,
        ))
