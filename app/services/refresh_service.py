"""Refresh token helpers.

Refresh tokens are opaque random strings stored in the DB (refresh_tokens table).
They are long-lived (default 30 days) and server-side revocable — unlike the
short-lived stateless JWT access token, which cannot be un-issued mid-life.

Revoke a refresh token to kill the session. Within one access-token lifetime
(default 1h) the tenant is still technically valid; after that it must
re-authenticate and will be denied.
"""

import secrets
import time
from typing import Optional

from app.models.refresh_token import RefreshToken

# 30 days in seconds
REFRESH_TTL = 60 * 60 * 24 * 30


async def create(identity_id: int, tenant: str) -> str:
    token = secrets.token_urlsafe(48)
    row = RefreshToken()
    row.token = token
    row.identity_id = int(identity_id)
    row.tenant = tenant
    row.expires_at = int(time.time()) + REFRESH_TTL
    row.revoked = False
    await row.save()
    return token


async def consume(token: str) -> Optional[RefreshToken]:
    """Validate a refresh token. Returns the row (with identity_id + tenant) or None."""
    row = await RefreshToken.where("token", token).first()
    if row is None or row.revoked:
        return None
    if int(row.expires_at) < int(time.time()):
        return None
    return row


async def revoke(token: str) -> None:
    row = await RefreshToken.where("token", token).first()
    if row:
        row.revoked = True
        await row.save()


async def revoke_all(identity_id: int) -> None:
    """Revoke every refresh token for a user (e.g. on password change)."""
    tokens = await RefreshToken.where("identity_id", int(identity_id)).where("revoked", False).get()
    for t in tokens:
        t.revoked = True
        await t.save()
