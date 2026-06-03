# Authenticating a tenant service against the Auth Service

This guide is for engineers building a **tenant service** (e.g. `tenant-a`,
`tenant-b`) that needs to authenticate users through the central **Auth Service**
and protect its own routes.

## Roles

| Component | Responsibility |
|---|---|
| **Auth Service** (this repo, the IdP) | Owns the **global** `identity` table + per-tenant memberships. Authenticates the user (once), keeps a central session, and **issues** JWTs — via the OAuth2 Authorization-Code flow (browser SSO) or a direct JSON API. |
| **Tenant service** (you) | Redirects the browser to the Auth Service to obtain a code, exchanges it for a JWT, creates its own local session, then **verifies** the JWT on its protected routes. |

The two share one secret: **`JWT_SECRET`** (HS256). The Auth Service signs with
it; every tenant service verifies with the same value. Tokens are standard JWTs,
so any language/library works (PyJWT, `firebase/php-jwt`, `jsonwebtoken`, …).

Users are **global**: one person, one credential. A tenant only sees a user once
that user is a **member** of it (granted by an admin, or seeded). Logging in once
at the IdP lets the user enter *any* tenant they're a member of **without
re-entering credentials** (single sign-on).

---

## Recommended: OAuth2 Authorization-Code SSO (browser, separate domains)

Use this when tenants are separate web apps on their own domains. The user logs in
once at the IdP; subsequent tenants get a token silently.

### Endpoints
| Method | Path | Caller | Purpose |
|---|---|---|---|
| GET | `/authorize` | browser | `?client_id&redirect_uri&response_type=code&state`. If logged in + member → redirects to `redirect_uri?code&state`; else shows `/login`. |
| GET/POST | `/login` | browser | IdP login page; establishes the central `idp_session` cookie. |
| POST | `/token` | tenant **backend** | `grant_type=authorization_code, code, redirect_uri, client_id, client_secret` → `{access_token, …}`. |
| GET | `/logout` | browser | Clears the central session (single sign-out). |

Each tenant is a **client**, registered in the IdP's config with a `client_id`, a
`client_secret`, and an exact-match **`redirect_uris` allowlist**.

### Sequence
```
1. user → tenant-a.com (no local session)
2. tenant-a redirects browser → IdP/authorize?client_id=tenant_a
        &redirect_uri=https://tenant-a.com/auth/callback&response_type=code&state=<random>
3. IdP: valid session? no → login page → user authenticates → idp_session cookie set
        member of tenant_a? no → 403
4. IdP redirects → https://tenant-a.com/auth/callback?code=<code>&state=<random>
5. tenant-a /auth/callback: check state, then BACK-CHANNEL:
        POST IdP/token {grant_type, code, client_id, client_secret, redirect_uri} → {access_token}
6. tenant-a creates its OWN local session for the user. Done.
7. later: user → tenant-b.com → step 2–6, but idp_session already exists →
        NO password prompt. Silent SSO. ✅
```

### Tenant-side: kick off login + handle the callback (FastAPI)
```python
import os, secrets, urllib.parse, httpx
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

IDP = "http://localhost:7700"
CLIENT_ID, CLIENT_SECRET = os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]  # must match the IdP allowlist exactly

# Send the user to the IdP
async def start_login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state            # tenant's own session
    q = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "response_type": "code", "state": state,
    })
    return RedirectResponse(f"{IDP}/authorize?{q}")

# IdP redirects back here with ?code&state
async def callback(request: Request):
    if request.query_params.get("state") != request.session.pop("oauth_state", None):
        raise HTTPException(400, "Bad state")            # CSRF guard
    code = request.query_params.get("code")
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{IDP}/token", data={
            "grant_type": "authorization_code", "code": code,
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        })
    r.raise_for_status()
    access_token = r.json()["access_token"]
    # Verify it (see below), then store identity in the tenant's local session.
    request.session["access_token"] = access_token
    return RedirectResponse("/")
```

The `access_token` you get back is the same HS256 JWT documented below — verify it
the same way (and confirm the `tenant` claim matches your tenant).

---

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

## Alternative: Direct JSON login (non-browser / API clients)

For server-to-server or trusted SPA clients that collect the password themselves
(no browser SSO), call `POST /auth/login` directly. The user must already be a
member of the requested tenant.

Base URL of the Auth Service (dev): `http://127.0.0.1:7700`.

### `POST /auth/login`

Request:
```json
{ "tenant": "tenant-a", "email": "multi@example.com", "password": "secret" }
```
- `email` is **global**; `tenant` is the slug you want a token for. The user must
  be a member of it.

Success `200`:
```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 3600 }
```
- `401` `{"detail":"Invalid credentials"}` — bad email/password (generic).
- `403` `{"detail":"User is not a member of this tenant"}` — valid user, no membership.
- `422` — missing/malformed fields.

### `GET /auth/me`  *(Bearer protected)*

Header: `Authorization: Bearer <jwt>`. Returns the global identity + the tenant
slugs it belongs to (password never included):
```json
{ "id": 1, "email": "multi@example.com", "name": "Multi Tenant User",
  "is_active": true, "tenants": ["tenant-a", "tenant-b"] }
```
`401` if the token is missing/invalid/expired.

### `POST /tenants/{slug}/members`  *(admin)*

A tenant grants a global user membership. Header `x-admin-secret: <ADMIN_SECRET>`,
form field `email` (+ optional `role`). `401` on bad secret, `404` if the user or
tenant is unknown.

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
