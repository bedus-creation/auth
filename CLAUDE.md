# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A tenant-aware authentication microservice. It validates `{tenant, email, password}`
against a shared Postgres `identity` table and issues HS256 JWTs that other tenant
services verify with the shared `JWT_SECRET`. Three endpoints (see `routes/api.py`):
`POST /auth/login`, `GET /auth/me` (Bearer-protected), `POST /auth/verify`.

The project is Python but follows a Laravel-style layout (`artisan`, `providers/`,
`config/`, `bootstrap/`, `databases/migrations` + `databases/seeds`). It is built on
the in-house **fastapi-startkit** framework, vendored as an editable local dependency
at `../../packages/fastapi-startkit-framework/fastapi_startkit` (see `pyproject.toml`
`[tool.uv.sources]`). The framework supplies the `Application` container, service
providers, the masoniteorm ORM/migrations, the `Router`/`FastAPIProvider`, and the
`env()` helper.

## Commands

Dependencies are managed with `uv`; the framework is not installed globally, so run
everything through `uv run` (a bare `python artisan` will fail with
`ModuleNotFoundError: No module named 'fastapi_startkit'`).

```bash
uv sync                          # install deps (incl. editable framework)
uv run python artisan serve      # run dev server on http://127.0.0.1:8000
uv run python artisan db:migrate # create tenants + identity tables
uv run python artisan seed       # seed tenant-a/tenant-b + demo identities
uv run python artisan            # list all available artisan commands

uv run pytest -v                 # run the test suite
uv run pytest path/to/test.py::test_name   # run a single test
```

Tests use `.env.testing` (SQLite at `storage/testing.sqlite`, no Postgres needed);
local dev uses `.env` (Postgres). Copy `.env.example` → `.env` and set `JWT_SECRET`
+ `DB_*` before first run.

## Architecture

**Boot flow.** `artisan` (or the ASGI entry) imports `bootstrap/application.py`, which
constructs the `Application` container with an ordered provider list. Order matters —
log → console → database → auth → fastapi. Each provider has `register()` (bind
services into the container) and `boot()` (run after all registers). `AppConfig`
(`config/app.py`) extends the framework's base config and nests `DatabaseConfig` +
`AuthConfig`; config dataclasses pull values via `env(...)` with defaults.

**Request path.** `FastAPIServiceProvider.boot()` mounts two routers from
`routes/api.py`: `public` (login, verify) and `protected` (a `Router` whose
`dependencies=[Depends(auth)]` enforce a Bearer token on every route). Routes point at
static methods on `AuthController`. The `auth` dependency (`app/http/dependencies/auth.py`)
parses the `Authorization: Bearer` header and returns decoded JWT claims or raises 401.

**Auth specifics worth knowing:**
- Login returns a deliberately generic 401 for *every* failure mode (unknown tenant,
  unknown email, inactive identity, bad password) so callers can't probe which field
  was wrong. Preserve this when editing `AuthController.login`.
- Email is unique **per tenant**, not globally — lookups always filter by `tenant_id`
  first (`identity` table has a `unique(["tenant_id","email"])` constraint and a
  cascading FK to `tenants`).
- Passwords use **bcrypt directly** via `app/services/hashing.py`. The framework's
  `Hash` facade is an unbound no-op, so do not route hashing through it.
- JWT logic lives in `app/services/jwt_service.py`. Two ways to get the service: the
  container binding `"jwt"` (set up in `providers/auth_provider.py`) and the
  module-level `get_jwt_service()` (an `lru_cache`d singleton built from `AuthConfig`).
  The controller/dependency use `get_jwt_service()`.
- `_pk(value)` in `auth_controller.py` normalizes inserted primary keys, because
  masoniteorm + asyncpg can return a PK as `{"id": n}` instead of a scalar. Use it
  whenever reading `.id` off a freshly created/fetched model.

**Models** (`app/models/`) are masoniteorm models, not SQLAlchemy. `Identity` declares
`__hidden__ = ["password"]` and `BelongsTo("Tenant")`; `Tenant` has `HasMany("Identity")`.
All DB calls are async (`await Identity.where(...).first()`, `await Identity.find(id)`).

**Migrations & seeds** live in `databases/` and are timestamp-prefixed
(`2026_06_03_000001_...`). `DatabaseSeeder` is the entry seeder and calls
`TenantSeeder` then `IdentitySeeder` in order.
