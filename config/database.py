from dataclasses import field
from typing import Any, Dict

from fastapi_startkit.environment import env
from fastapi_startkit.masoniteorm import PostgresConfig, SQLiteConfig
from pydantic.dataclasses import dataclass


@dataclass
class DatabaseConfig:
    default: str = field(default_factory=lambda: env("DB_CONNECTION", "postgres"))

    connections: dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "postgres": PostgresConfig(
            driver="postgres",
            host=env("DB_HOST", "127.0.0.1"),
            port=int(env("DB_PORT", "5432")),
            database=env("DB_DATABASE", "auth_db"),
            username=env("DB_USERNAME", "postgres"),
            password=env("DB_PASSWORD", ""),
        ),
        # Used by the test suite. An explicit url is required because the
        # connection factory otherwise builds a host:port sqlite URL that
        # SQLAlchemy rejects. File-based (not :memory:) so data survives the
        # NullPool reconnects the test harness uses.
        "sqlite": SQLiteConfig(
            driver="sqlite",
            url=env("DB_URL", "sqlite+aiosqlite:///storage/testing.sqlite"),
            database=env("DB_DATABASE", "storage/testing.sqlite"),
        ),
    })
