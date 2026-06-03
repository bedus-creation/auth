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

```bash
uv sync

# Postgres (or use your own):
docker run -d --name auth-pg \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=auth_db \
  -p 5432:5432 postgres:16

cp .env.example .env            # set JWT_SECRET + DB_* to taste

python artisan db:migrate       # create tenants + identity tables
python artisan seed             # seed tenant-a / tenant-b + demo identities
python artisan serve            # http://127.0.0.1:8000

curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"tenant-a","email":"admin@tenant-a.com","password":"secret"}'
```

The issued token is a standard HS256 JWT — any compliant library (PyJWT,
`firebase/php-jwt`, jsonwebtoken, ...) can verify it with the shared secret.

## Tests

```bash
uv run pytest -v
```
