from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models as _models  # noqa: F401
from .api import router
from .config import Settings, get_settings
from .database import Base, build_engine, build_session_factory
from .middleware import RequestBodyLimitMiddleware
from .retention import enforce_retention


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    engine = build_engine(runtime_settings.database_url)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    docs_url = "/docs" if runtime_settings.docs_enabled else None
    redoc_url = "/redoc" if runtime_settings.docs_enabled else None
    openapi_url = "/openapi.json" if runtime_settings.docs_enabled else None
    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.state.engine = engine
    application.state.session_factory = session_factory
    application.add_middleware(
        RequestBodyLimitMiddleware,
        api_prefix=runtime_settings.api_prefix,
        max_upload_bytes=runtime_settings.max_upload_mb * 1024 * 1024,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(
        router,
        prefix=runtime_settings.api_prefix,
        dependencies=[Depends(enforce_retention)],
    )
    if runtime_settings.static_dir is not None:
        static_root = Path(runtime_settings.static_dir)
        if not static_root.is_dir():
            raise ValueError(f"EAV_STATIC_DIR is not a directory: {static_root}")
        # Registered after the API router, so /api/v1 and /docs keep priority.
        application.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")
    return application


app = create_app()
