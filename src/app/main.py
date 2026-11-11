"""Application factory and the ASGI application served by uvicorn."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, items
from app.api.health import ReadinessCheck
from app.cache import CachedItemRepository, create_cache
from app.config import Settings
from app.db import Database, SqlItemRepository
from app.log import RequestLoggingMiddleware, configure_logging
from app.metrics import setup_metrics
from app.rate_limit import RateLimitMiddleware
from app.repository import ItemRepository
from app.security import require_auth
from app.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Release connections when the server shuts down."""
    yield
    await app.state.cache.close()
    await app.state.database.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application. Nothing here opens a network connection."""
    settings = settings or Settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    readiness_checks: dict[str, ReadinessCheck] = {}

    database = Database(settings.database_url)
    app.state.database = database
    readiness_checks["database"] = database.ping
    repository: ItemRepository = SqlItemRepository(database.sessions)

    cache = create_cache(settings.redis_url)
    app.state.cache = cache
    readiness_checks["cache"] = cache.ping
    repository = CachedItemRepository(repository, cache, settings.cache_ttl_seconds)

    app.state.repository = repository
    app.state.readiness_checks = readiness_checks

    # The middleware added last sees the request first.
    setup_metrics(app)
    app.add_middleware(RateLimitMiddleware, limit=settings.rate_limit)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(items.router, prefix="/api/v1", dependencies=[Depends(require_auth)])
    return app


app = create_app()
