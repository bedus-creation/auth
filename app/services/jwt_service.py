"""JWT issuing/verification (HS256 by default).

Tokens are standard JWTs, so any compliant verifier (PyJWT, firebase/php-jwt,
jsonwebtoken, ...) can validate them given the same shared secret + algorithm.
"""

import datetime as dt
from functools import lru_cache
from typing import Any, Optional

import jwt

from config.auth import AuthConfig


class JwtService:
    def __init__(self, secret: str, algorithm: str = "HS256", ttl: int = 3600):
        self.secret = secret
        self.algorithm = algorithm
        self.ttl = ttl

    def issue(
        self,
        *,
        subject: Any,
        tenant: str,
        tenant_id: int,
        email: str,
        extra: Optional[dict] = None,
    ) -> str:
        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "sub": str(subject),
            "tenant": tenant,
            "tenant_id": tenant_id,
            "email": email,
            "iat": now,
            "exp": now + dt.timedelta(seconds=self.ttl),
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, token: str) -> dict:
        """Decode + verify a token. Raises jwt.PyJWTError on invalid/expired."""
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])


@lru_cache(maxsize=1)
def get_jwt_service() -> JwtService:
    """Lazily build a JwtService from AuthConfig (env is loaded by app boot)."""
    config = AuthConfig()
    return JwtService(
        secret=config.jwt_secret,
        algorithm=config.jwt_algorithm,
        ttl=config.jwt_ttl,
    )
