FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv --quiet

WORKDIR /app
COPY . .

RUN uv sync --no-dev --quiet

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 7700
CMD ["/app/entrypoint.sh"]
