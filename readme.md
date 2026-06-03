# Auth Service

A tenant-aware authentication / SSO microservice built on the **fastapi-startkit**
framework.

It is an OAuth2 Authorization-Code **Identity Provider (IdP)** with a central login
session and cross-tenant **SSO**, plus a direct JSON login API. Users are **global**;
a tenant grants membership. On successful auth it issues an **HS256 JWT** that tenant
services verify with the shared `JWT_SECRET`.

For the full tenant-side integration guide, see
[`docs/tenant-authentication.md`](docs/tenant-authentication.md).

## How to run the project

### Requirements

- [`uv`](https://docs.astral.sh/uv/) — dependencies and the Python toolchain are
  managed with `uv`. Python is pinned to **3.13** via `.python-version`, and
  `uv sync` provisions it for you.
- No database server is required for local dev: it uses **SQLite**
  (`storage/auth.sqlite`).

> **Important:** the framework (`fastapi-startkit`) is an *editable local
> dependency*, not globally installed. Everything must run through `uv run`.
> A bare `python artisan ...` fails with
> `ModuleNotFoundError: No module named 'fastapi_startkit'`.

### Quick start

```bash
uv sync                                       # install deps + provision Python 3.13
cp .env.example .env                          # then set secrets if desired

uv run python artisan db:migrate              # create tables
uv run python artisan db:seed                 # seed demo tenants + accounts
uv run python artisan serve --port 7700       # http://127.0.0.1:7700
```

> Note: it is `db:seed`, **not** `seed`. Bare `seed` only scaffolds a new
> seeder file; `db:seed` runs the seeders.

Open the authorization flow in a browser:

```
http://localhost:7700/authorize?client_id=tenant-a&redirect_uri=http://localhost/auth/callback&response_type=code&state=xyz
```

The login page is server-rendered and, in dev, is prefilled with demo credentials.

### Rebuild the schema from scratch

```bash
uv run python artisan db:migrate:fresh
uv run python artisan db:seed
```

`db:migrate` creates the `tenants`, `identity`, `identity_tenant`, and `auth_codes`
tables.

### Using Postgres instead of SQLite

Postgres is supported via `config/database.py`. In `.env` set:

```dotenv
DB_CONNECTION=postgres
DB_HOST=...
DB_PORT=...
DB_DATABASE=...
DB_USERNAME=...
DB_PASSWORD=...
```

Then re-run `db:migrate` + `db:seed`.

## Demo data

Tenant clients (`client_id`): **`tenant-a`** and **`tenant-b`** (the underscore
forms `tenant_a` / `tenant_b` are also accepted). Their client secrets default to
`tenant-a-client-secret` / `tenant-b-client-secret` (see `.env`).

Demo login accounts (all with password `secret`):

| Email                 | Membership          |
|-----------------------|---------------------|
| `multi@example.com`   | tenant-a + tenant-b |
| `only-a@example.com`  | tenant-a only       |
| `only-b@example.com`  | tenant-b only       |

## Endpoints

**Browser (front-channel)**

| Method   | Path         | Notes                                                          |
|----------|--------------|----------------------------------------------------------------|
| GET      | `/authorize` | Params: `client_id`, `redirect_uri`, `response_type=code`, `state` |
| GET/POST | `/login`     | Server-rendered; prefilled with demo creds in dev              |
| GET      | `/logout`    | Clears the central login session                               |

**Back-channel**

| Method | Path     | Notes                                                                                         |
|--------|----------|-----------------------------------------------------------------------------------------------|
| POST   | `/token` | `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret` → HS256 JWT |

**JSON API**

| Method | Path           | Notes                                  |
|--------|----------------|----------------------------------------|
| POST   | `/auth/login`  | Body `{tenant, email, password}` → JWT |
| GET    | `/auth/me`     | Bearer token → identity                |
| POST   | `/auth/verify` | Validate a token, return its claims    |

**Admin**

| Method | Path                      | Notes                            |
|--------|---------------------------|----------------------------------|
| POST   | `/tenants/{slug}/members` | Requires header `x-admin-secret` |

Example direct login:

```bash
curl -s -X POST localhost:7700/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"tenant-a","email":"only-a@example.com","password":"secret"}'
```

The issued token is a standard HS256 JWT — any compliant library (PyJWT,
`firebase/php-jwt`, jsonwebtoken, ...) can verify it with the shared `JWT_SECRET`.

## Troubleshooting

- **`/token` → 401 "Invalid client credentials"** — the `client_secret` is wrong or
  missing. Use `TENANT_A_CLIENT_SECRET` / `TENANT_B_CLIENT_SECRET` from `.env`
  (defaults `tenant-a-client-secret` / `tenant-b-client-secret`).
- **`/auth/login` → 401 "Invalid credentials"** — bad email/password, or a wrong
  `tenant` slug (use `tenant-a`, and one of the demo accounts above).
- **`/token` → 400 "Invalid or expired code"** — codes are single-use and short-lived;
  send the **same** `client_id` and `redirect_uri` you used at `/authorize`.
- **`client_id`** accepts both `tenant-a` and `tenant_a` (hyphen or underscore).
- **`redirect_uri`** allowlist matching is **disabled in dev** (any URL is accepted).
  Re-enable it in `app/services/oauth.py` (`validate_redirect_uri`) before production.
- **A tenant rejects the JWT** — the tenant's `JWT_SECRET` must be identical to the
  IdP's `JWT_SECRET`.

## Tests

There are currently no automated tests in this project.
