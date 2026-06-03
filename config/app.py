from dataclasses import field

from fastapi_startkit.config import AppConfig as BaseConfig
from pydantic.dataclasses import dataclass

from config.auth import AuthConfig
from config.database import DatabaseConfig


@dataclass
class AppConfig(BaseConfig):
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
