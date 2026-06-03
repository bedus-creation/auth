FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv --quiet

COPY packages/fastapi-startkit-framework /packages/fastapi-startkit-framework

WORKDIR /app
COPY tenants/auth .

RUN cp .env.example .env
RUN uv sync --no-dev --quiet

COPY tenants/auth/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 7700
CMD ["/app/entrypoint.sh"]
