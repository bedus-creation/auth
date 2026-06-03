#!/bin/sh
set -e

# Bootstrap .env from the example if it doesn't exist yet (fresh environment).
if [ ! -f /app/.env ]; then
  echo "▶ No .env found — copying .env.example..."
  cp /app/.env.example /app/.env
fi

echo "▶ Running migrations..."
uv run python artisan db:migrate

echo "▶ Seeding database..."
uv run python artisan db:seed || echo "  (seed skipped — data already exists)"

echo "▶ Starting auth service on 0.0.0.0:7700..."
exec uv run python artisan serve --host 0.0.0.0 --port 7700
