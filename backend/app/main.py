from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.database import configure_database, create_schema
from app.core.metrics import MetricsMiddleware, metrics_response
from app.core.middleware import RequestIdMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_database(settings.DATABASE_URL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.AUTO_CREATE_TABLES:
            create_schema()
        yield

    app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": settings.APP_NAME, "docs": "/docs", "health": f"{settings.API_V1_PREFIX}/health/ready"}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return metrics_response()

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
