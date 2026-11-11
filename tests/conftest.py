"""Fixtures shared by all tests."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.db import Base
from app.main import create_app
from app.security import create_access_token


@pytest.fixture
def settings() -> Settings:
    """Settings that ignore a local .env file and use an in-memory SQLite database."""
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite://",
        rate_limit="1000/minute",
    )


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        async with application.state.database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield application


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    """Headers that authenticate a request."""
    token = create_access_token(settings.auth_username, settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(app: FastAPI, auth_headers: dict[str, str]) -> AsyncIterator[AsyncClient]:
    """HTTP client that calls the application in process as an authenticated caller."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_headers
    ) as client:
        yield client


@pytest.fixture
async def anonymous_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """HTTP client that sends no credentials."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
