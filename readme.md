# Auth Service

A **multi-tenant authentication microservice** built on the
[fastapi-startkit](https://pypi.org/project/fastapi-startkit/) framework.

Users are **global** — one account, one password. A tenant grants a user
**membership**, and the auth service issues a tenant-scoped **HS256 JWT** that
the tenant service verifies locally with the shared `JWT_SECRET`.

---

## How to run

> **All commands go through `uv run`.**  
> `fastapi-startkit` is an editable local dep, not globally installed — a bare
> `python artisan …` fails with `ModuleNotFoundError`.

```bash
uv sync                                  # install deps + provision Python 3.13
cp .env.example .env                     # adjust JWT_SECRET + ADMIN_SECRET

uv run python artisan db:migrate         # create tables
uv run python artisan db:seed            # seed demo tenants + users
uv run python artisan serve --port 7700  # http://127.0.0.1:7700
```

> Use `db:seed` — bare `seed` only scaffolds a seeder file.

### Reset the database

```bash
uv run python artisan db:migrate:fresh   # drop + recreate all tables
uv run python artisan db:seed
```

### Postgres (optional)

SQLite is the default (no server needed). To use Postgres set in `.env`:

```dotenv
DB_CONNECTION=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=auth_db
DB_USERNAME=postgres
DB_PASSWORD=postgres
```

---

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/login` | — | `{tenant, email, password}` → JWT |
| POST | `/auth/verify` | — | Validate a token, return its claims |
| GET  | `/auth/me` | Bearer | Return the logged-in identity + their tenants |
| POST | `/tenants/{slug}/members` | `x-admin-secret` header | Add a user to a tenant |

---

## Demo accounts

All passwords are `secret`.

| Email | Tenant access |
|-------|--------------|
| `multi@example.com` | tenant-a **and** tenant-b |
| `only-a@example.com` | tenant-a only |
| `only-b@example.com` | tenant-b only |

```bash
# Login
curl -s -X POST http://localhost:7700/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"tenant-a","email":"multi@example.com","password":"secret"}'

# Authenticated request
curl -s http://localhost:7700/auth/me \
  -H "Authorization: Bearer <token>"

# Add a user to a tenant
curl -s -X POST http://localhost:7700/tenants/tenant-b/members \
  -H "x-admin-secret: dev-admin-secret-change-me" \
  --data-urlencode email=only-a@example.com
```

---

## JWT

Tokens are standard **HS256 JWTs**. Claims:

```json
{ "sub": "1", "tenant": "tenant-a", "email": "multi@example.com", "iat": …, "exp": … }
```

Any compliant library verifies them with `JWT_SECRET`:
- Python: `PyJWT` — `jwt.decode(token, secret, algorithms=["HS256"])`
- PHP: `firebase/php-jwt` — `JWT::decode($token, new Key($secret, 'HS256'))`
- Node: `jsonwebtoken` — `jwt.verify(token, secret, { algorithms: ["HS256"] })`

Always check the `tenant` claim matches the tenant the request is for.

---

## Tenant integration

See [`docs/tenant-authentication.md`](docs/tenant-authentication.md).

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Invalid credentials` | Wrong email/password or wrong tenant slug | Use `tenant-a` (hyphen), valid account |
| `403 not a member` | User exists but isn't in that tenant | Add them via `POST /tenants/{slug}/members` |
| `401` on JWT verify in tenant | Wrong `JWT_SECRET` | Must match the auth service's `JWT_SECRET` exactly |
