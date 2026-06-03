FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv --quiet

# Copy the local fastapi-startkit package so the editable path resolves.
# pyproject.toml references ../../packages/fastapi-startkit-framework/fastapi_startkit
# which from WORKDIR /app resolves to /packages/fastapi-startkit-framework/fastapi_startkit.
COPY packages/fastapi-startkit-framework /packages/fastapi-startkit-framework

WORKDIR /app
COPY tenants/auth .

# .env.example is the base config; docker-compose environment vars override it.
RUN cp .env.example .env
RUN uv sync --no-dev --quiet

COPY tenants/auth/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 7700
CMD ["/app/entrypoint.sh"]
