"""OAuth2 authorization-code helpers: client registry lookup, redirect_uri
validation, and one-time code create/consume backed by the auth_codes table."""

import hmac
import secrets
import time
from typing import Optional

from app.models.auth_code import AuthCode
from config.auth import AuthConfig


def _config() -> AuthConfig:
    return AuthConfig()


def get_client(client_id: Optional[str]) -> Optional[dict]:
    if not client_id:
        return None
    return _config().clients.get(client_id)


def validate_redirect_uri(client: Optional[dict], redirect_uri: Optional[str]) -> bool:
    """Exact-match against the client's allowlist (no prefix/substring matching)."""
    if not client or not redirect_uri:
        return False
    return redirect_uri in client.get("redirect_uris", [])


def verify_client_secret(client: Optional[dict], client_secret: Optional[str]) -> bool:
    expected = (client or {}).get("secret", "")
    return bool(expected) and hmac.compare_digest(str(expected), str(client_secret or ""))


async def create_code(identity_id: int, client_id: str, redirect_uri: str) -> str:
    code = secrets.token_urlsafe(32)
    row = AuthCode()
    row.code = code
    row.identity_id = identity_id
    row.client_id = client_id
    row.redirect_uri = redirect_uri
    row.expires_at = int(time.time()) + _config().auth_code_ttl
    row.used = False
    await row.save()
    return code


async def consume_code(code: str, client_id: str, redirect_uri: str) -> Optional[int]:
    """Validate + single-use a code. Returns the identity_id on success, else None."""
    row = await AuthCode.where("code", code).first()
    if row is None or row.used:
        return None
    if int(row.expires_at) < int(time.time()):
        return None
    if row.client_id != client_id or row.redirect_uri != redirect_uri:
        return None
    row.used = True
    await row.save()
    return int(row.identity_id)
