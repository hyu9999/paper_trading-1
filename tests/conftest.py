import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings


@pytest.fixture
def app() -> FastAPI:
    from app.main import app
    return app


@pytest.fixture
async def initialized_app(app: FastAPI) -> FastAPI:
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        app=initialized_app,
        base_url=settings.base_url,
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture
async def db(initialized_app: FastAPI) -> AsyncIOMotorDatabase:
    return initialized_app.state.db[settings.db.name]
