from pathlib import Path

from fastapi_startkit.application import Application
from fastapi_startkit.exceptions import ExceptionHandler
from fastapi_startkit.logging.providers import LogProvider
from fastapi_startkit.masoniteorm.providers import DatabaseProvider

from config.app import AppConfig
from config.database import DatabaseConfig
from config.logging import LoggingConfig
from providers.auth_provider import AuthProvider
from providers.console_provider import ConsoleProvider
from providers.fastapi_provider import FastAPIServiceProvider


class AppExceptionHandler(ExceptionHandler):
    def register(self):
        pass


app: Application[AppConfig] = Application(
    base_path=Path(__file__).parent.parent,
    config=AppConfig,
    providers=[
        (LogProvider, LoggingConfig),
        ConsoleProvider,
        (DatabaseProvider, DatabaseConfig),
        AuthProvider,
        FastAPIServiceProvider,
    ],
    exception_handler=AppExceptionHandler,
)
