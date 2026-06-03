# Authenticating a tenant service against the Auth Service

This guide is for engineers building a **tenant service** (e.g. `tenant-a`,
`tenant-b`) that needs to authenticate users through the central **Auth Service**
and protect its own routes.

## Roles

| Component | Responsibility |
|---|---|
| **Auth Service** (this repo) | Owns the `identity` table. Validates `{tenant, email, password}` and **issues** signed JWTs. |
| **Tenant service** (you) | Sends users to the Auth Service to log in, then **verifies** the JWT on each request to its own protected routes. |

The two share one secret: **`JWT_SECRET`** (HS256). The Auth Service signs with
it; every tenant service verifies with the same value. Tokens are standard JWTs,
so any language/library works (PyJWT, `firebase/php-jwt`, `jsonwebtoken`, …).

## Flow

```
 user            tenant service                 auth service
  |   credentials     |                              |
  |------------------>|                              |
  |                   |  POST /auth/login            |
  |                   |  {tenant, email, password}   |
  |                   |----------------------------->|
  |                   |   200 {access_token}         |
  |                   |<-----------------------------|
  |  token (cookie/   |                              |
  |   header)         |                              |
  |<------------------|                              |
  |                   |                              |
  |  request + Bearer |                              |
  |------------------>|  verify JWT locally          |
  |                   |  (shared secret, no network) |
  |   200 / 401       |                              |
  |<------------------|                              |
```

The tenant service **verifies tokens locally** — no network call to the Auth
Service per request. The Auth Service is only contacted at login.

## Endpoint reference

Base URL of the Auth Service (dev): `http://127.0.0.1:8000`.

### `POST /auth/login`

Request:
```json
{ "tenant": "tenant-a", "email": "admin@tenant-a.com", "password": "secret" }
```
- `tenant` — the tenant **slug** the identity belongs to (an email is unique
  *per tenant*, not globally).

Success `200`:
```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 3600 }
```
Failure `401` (generic, never reveals which field was wrong):
```json
{ "detail": "Invalid credentials" }
```
Validation error `422` (missing/malformed fields).

### `GET /auth/me`  *(Bearer protected)*

Header: `Authorization: Bearer <jwt>`. Returns the identity (password never
included):
```json
{ "id": 1, "tenant": "tenant-a", "email": "admin@tenant-a.com",
  "name": "Tenant A Admin", "is_active": true }
```
`401` if the token is missing/invalid/expired.

### `POST /auth/verify`

For services that prefer a remote check instead of verifying locally.
```json
{ "token": "<jwt>" }
```
Success `200`:
```json
{ "valid": true, "claims": { "sub": "1", "tenant": "tenant-a",
  "email": "admin@tenant-a.com", "iat": 1780000000, "exp": 1780003600 } }
```
`401` if the token is invalid or expired.

## JWT claims

```json
{
  "sub":    "1",                  // identity id (string)
  "tenant": "tenant-a",           // tenant slug — scope your data by this
  "email":  "admin@tenant-a.com",
  "iat":    1780000000,           // issued-at (unix seconds)
  "exp":    1780003600            // expiry (iat + JWT_TTL)
}
```
- Algorithm: **HS256**. Verifiers must pin `algorithms=["HS256"]` (never trust
  the token's own `alg` header / "none").
- `exp` is enforced by any standard verifier.
- **Always check `tenant`** matches the tenant the request is for — a valid token
  for `tenant-b` must not be accepted by `tenant-a`.

## Verifying tokens in a tenant service

### Configuration (every tenant service)

```
JWT_SECRET=<the exact same value as the Auth Service>
JWT_ALGORITHM=HS256
```
Keep the secret in env/secret manager, never in source. Generate with
`openssl rand -hex 32` (≥ 32 bytes).

### Python (FastAPI) — local verification dependency

```python
# auth.py  (in the tenant service)
import os
import jwt
from fastapi import Header, HTTPException

JWT_SECRET = os.environ["JWT_SECRET"]
THIS_TENANT = os.environ["TENANT_SLUG"]  # e.g. "tenant-a"

def current_identity(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token",
                            headers={"WWW-Authenticate": "Bearer"})
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"})
    if claims.get("tenant") != THIS_TENANT:
        raise HTTPException(403, "Token not valid for this tenant")
    return claims

# usage
# @app.get("/dashboard")
# async def dashboard(identity: dict = Depends(current_identity)):
#     return {"user_id": identity["sub"], "email": identity["email"]}
```

### PHP — `firebase/php-jwt`

```php
// composer require firebase/php-jwt
use Firebase\JWT\JWT;
use Firebase\JWT\Key;

function currentIdentity(string $bearer): array {
    $secret     = getenv('JWT_SECRET');
    $thisTenant = getenv('TENANT_SLUG');     // e.g. "tenant-a"

    $token = preg_replace('/^Bearer\s+/i', '', $bearer);
    try {
        $claims = JWT::decode($token, new Key($secret, 'HS256'));  // checks exp + signature
    } catch (\Throwable $e) {
        http_response_code(401);
        exit(json_encode(['detail' => 'Invalid or expired token']));
    }
    if (($claims->tenant ?? null) !== $thisTenant) {
        http_response_code(403);
        exit(json_encode(['detail' => 'Token not valid for this tenant']));
    }
    return (array) $claims; // sub, tenant, email, iat, exp
}
```

### Node — `jsonwebtoken`

```js
const jwt = require("jsonwebtoken");
function currentIdentity(authHeader) {
  const token = (authHeader || "").replace(/^Bearer\s+/i, "");
  const claims = jwt.verify(token, process.env.JWT_SECRET, { algorithms: ["HS256"] });
  if (claims.tenant !== process.env.TENANT_SLUG) throw new Error("wrong tenant");
  return claims; // throws on invalid/expired
}
```

### Alternative: remote verification

If you’d rather not share the secret with a tenant service, call
`POST /auth/verify` instead of verifying locally. Trade-off: a network round-trip
per request (cache it for the token’s lifetime) and the tenant must reach the Auth
Service. For untrusted verifiers, prefer migrating the Auth Service to **RS256**
and handing out only the public key — then no shared secret is needed.

## Security checklist

- [ ] `JWT_SECRET` identical across Auth + tenant services, ≥ 32 bytes, in secrets
      management — not in git.
- [ ] Verifiers pin `algorithms=["HS256"]`.
- [ ] Verifiers enforce `exp` (standard libs do) and check the `tenant` claim.
- [ ] All traffic over HTTPS in production (the token is a bearer credential).
- [ ] Decide token storage on the client (httpOnly cookie vs. Authorization header).
- [ ] Tokens currently expire after `JWT_TTL` (default 1h) with **no refresh
      endpoint yet** — users re-login on expiry. Add refresh tokens if you need
      longer sessions.

## Not yet implemented (roadmap)

The broader SSO vision (central session cookie at the IdP, OAuth-style auth-code
flow, backend token exchange, refresh tokens) is described in
[`../architecutre.md`](../architecutre.md). Today the Auth Service implements the
credential-login + JWT-issuance core of that design.
