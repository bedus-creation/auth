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
