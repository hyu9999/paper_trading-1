import pytest
from fastapi import FastAPI
from dynaconf import Dynaconf
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings as base_settings
from app.models.domain.users import UserInDB
from app.db.repositories.user import UserRepository


@pytest.fixture
def settings() -> Dynaconf:
    base_settings.setenv("testing")
    return base_settings


@pytest.fixture
def app() -> FastAPI:
    from app.main import app
    return app


@pytest.fixture
async def initialized_app(app: FastAPI) -> FastAPI:
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(initialized_app: FastAPI, settings: Dynaconf) -> AsyncClient:
    async with AsyncClient(
        app=initialized_app,
        base_url=settings.base_url,
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture
async def db(initialized_app: FastAPI, settings: Dynaconf) -> AsyncIOMotorDatabase:
    return initialized_app.state.db[settings.db.name]


@pytest.fixture
async def test_user(db: AsyncIOMotorDatabase) -> UserInDB:
    return await UserRepository(db).create_user(capital=10000000)
