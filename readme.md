# Auth Service

Tenant-aware authentication service built on the **fastapi-startkit** framework.
It validates credentials against the shared Postgres `identity` table and, on
success, issues an HS256 JWT that tenant services verify with the shared
`JWT_SECRET`.

## Endpoints

| Method | Path          | Purpose                                            |
|--------|---------------|----------------------------------------------------|
| POST   | `/auth/login` | Validate `{tenant, email, password}` → issue a JWT |
| GET    | `/auth/me`    | Return the identity for a valid Bearer token       |
| POST   | `/auth/verify`| Validate a token, return its claims                |

## Quick start

Local dev runs on SQLite — no database server required.

```bash
uv sync
cp .env.example .env                  # set JWT_SECRET; SQLite is the default

uv run python artisan db:migrate      # create tenants + identity tables
uv run python artisan db:seed         # seed tenant-a / tenant-b + demo identities
uv run python artisan serve --port 8000

curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"tenant-a","email":"admin@tenant-a.com","password":"secret"}'
```

Demo identities (password `secret`): `admin@tenant-a.com`, `user@tenant-a.com`,
`admin@tenant-b.com`.

### Using Postgres instead

```bash
docker run -d --name auth-pg \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=auth_db \
  -p 5432:5432 postgres:16
```

Then in `.env` set `DB_CONNECTION=postgres` and the `DB_HOST/DB_PORT/DB_DATABASE/
DB_USERNAME/DB_PASSWORD` vars, and re-run `db:migrate` + `db:seed`.

The issued token is a standard HS256 JWT — any compliant library (PyJWT,
`firebase/php-jwt`, jsonwebtoken, ...) can verify it with the shared secret.

## Tests

```bash
uv run pytest -v
```
