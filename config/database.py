from dataclasses import field
from typing import Any, Dict

from fastapi_startkit.environment import env
from fastapi_startkit.masoniteorm import PostgresConfig, SQLiteConfig
from pydantic.dataclasses import dataclass


@dataclass
class DatabaseConfig:
    # Defaults to SQLite so the project runs with no database server. Override
    # with DB_CONNECTION=postgres (+ DB_HOST/... ) in .env to use Postgres.
    default: str = field(default_factory=lambda: env("DB_CONNECTION", "sqlite"))

    connections: dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        # An explicit url is required because the connection factory otherwise
        # builds a host:port sqlite URL that SQLAlchemy rejects. File-based.
        "sqlite": SQLiteConfig(
            driver="sqlite",
            url=env("DB_URL", "sqlite+aiosqlite:///storage/auth.sqlite"),
            database=env("DB_DATABASE", "storage/auth.sqlite"),
        ),
        "postgres": PostgresConfig(
            driver="postgres",
            host=env("DB_HOST", "127.0.0.1"),
            port=int(env("DB_PORT", "5432")),
            database=env("DB_DATABASE", "auth_db"),
            username=env("DB_USERNAME", "postgres"),
            password=env("DB_PASSWORD", ""),
        ),
    })
