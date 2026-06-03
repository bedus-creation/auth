from fastapi import FastAPI
from fastapi_startkit.fastapi import FastAPIProvider


class FastAPIServiceProvider(FastAPIProvider):
    def register(self) -> None:
        from fastapi_startkit.fastapi.config import FastAPIConfig

        config = self.resolve_config(FastAPIConfig)
        self.merge_config_from(config, self.provider_key)

        fastapi = FastAPI(
            title="Auth Service",
            version="1.0.0",
        )
        self.app.use_fastapi(fastapi)

    def boot(self) -> None:
        super().boot()

        from routes.api import public, protected

        self.app.include_router(public.router)
        self.app.include_router(protected.router)

        self._register_http_exception_handler()

    def _register_http_exception_handler(self) -> None:
        """Return real HTTP status codes for HTTPException.

        The framework's default handler renders every HTTPException as a 500, so
        we register our own (later registration wins) that preserves the status
        code, detail and headers (e.g. WWW-Authenticate on 401).
        """
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        from starlette.exceptions import HTTPException as StarletteHTTPException

        async def handle_http_exception(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None),
            )

        self.app.fastapi.add_exception_handler(HTTPException, handle_http_exception)
        self.app.fastapi.add_exception_handler(StarletteHTTPException, handle_http_exception)
