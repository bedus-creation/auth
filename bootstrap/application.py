from pathlib import Path

from fastapi_startkit.application import Application
from fastapi_startkit.exceptions import ExceptionHandler
from fastapi_startkit.logging.providers import LogProvider
from fastapi_startkit.masoniteorm.providers import DatabaseProvider
from starlette.middleware.sessions import SessionMiddleware

from config.app import AppConfig
from config.auth import AuthConfig
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

# Central IdP session (signed httpOnly cookie). `lax` lets the cookie ride the
# top-level redirect from a tenant into /authorize so SSO works across domains.
app.add_middleware(
    SessionMiddleware,
    secret_key=AuthConfig().session_secret,
    session_cookie="idp_session",
    same_site="lax",
    https_only=False,  # set True behind HTTPS in production
)
