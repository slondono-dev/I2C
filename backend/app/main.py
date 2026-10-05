from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.ai import get_orchestrator
from app.ai.factory import load_overrides_from_db
from app.ai.health_monitor import run_forever
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.ratelimit import limiter

log = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    configure_logging()
    if s.is_production and s.secret_key == "change-me-in-production":
        raise RuntimeError("SECRET_KEY must be set in production")
    Path(s.media_root).mkdir(parents=True, exist_ok=True)
    try:
        load_overrides_from_db(get_orchestrator())
    except Exception as exc:  # DB may not be migrated yet on first boot
        log.warning("ai.overrides_not_loaded", error=str(exc))
    log.info("app.start", mode=s.app_mode, features=s.feature_flags())
    monitor = None
    if s.app_mode != "test":
        monitor = asyncio.create_task(
            run_forever(get_orchestrator(), s.health_check_interval_seconds)
        )
    yield
    if monitor:
        monitor.cancel()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    if s.storage_provider == "local":
        Path(s.media_root).mkdir(parents=True, exist_ok=True)
        app.mount(s.media_url, StaticFiles(directory=str(s.media_root)), name="media")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "mode": s.app_mode, "features": s.feature_flags()}

    return app


app = create_app()
