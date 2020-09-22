import asyncio

import pytest
from fastapi import FastAPI
from dynaconf import Dynaconf
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings as base_settings
from app.models.domain.users import UserInDB
from app.db.repositories.user import UserRepository


@pytest.yield_fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Dynaconf:
    base_settings.setenv("testing")
    return base_settings


@pytest.fixture(scope="session")
def app() -> FastAPI:
    from app.main import app
    return app


@pytest.fixture(scope="session")
async def initialized_app(app: FastAPI) -> FastAPI:
    async with LifespanManager(app):
        yield app


@pytest.fixture(scope="session")
async def client(initialized_app: FastAPI, settings: Dynaconf, event_loop) -> AsyncClient:
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
