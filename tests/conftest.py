import asyncio

import pytest
from fastapi import FastAPI
from dynaconf import Dynaconf
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings as base_settings
from app.core import jwt
from app.db.repositories.user import UserRepository
from app.models.domain.users import UserInDB
from app.services.engines.event_engine import EventEngine

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
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
    async with LifespanManager(app, startup_timeout=30):
        yield app


@pytest.fixture(scope="session")
async def client(initialized_app: FastAPI, settings: Dynaconf,
                 event_loop: asyncio.AbstractEventLoop) -> AsyncClient:
    async with AsyncClient(
        app=initialized_app,
        base_url=settings.base_url,
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


@pytest.fixture(scope="session")
async def db(initialized_app: FastAPI, settings: Dynaconf) -> AsyncIOMotorDatabase:
    return initialized_app.state.db[settings.db.name]


@pytest.fixture(scope="session")
async def test_user(db: AsyncIOMotorDatabase) -> UserInDB:
    return await UserRepository(db).create_user(capital=10000000)


@pytest.fixture(scope="session")
def token(test_user: UserInDB, settings: Dynaconf) -> str:
    return jwt.create_access_token_for_user(test_user.id)


@pytest.fixture(scope="session")
def authorized_client(
    client: AsyncClient, token: str, settings: Dynaconf
) -> AsyncClient:
    client.headers = {
        "Authorization": f"{settings.token_prefix} {token}",
        **client.headers,
    }
    return client


@pytest.fixture
async def test_user_scope_func(db: AsyncIOMotorDatabase) -> UserInDB:
    """测试用户, 作用域为func"""
    return await UserRepository(db).create_user(capital=10000000)


@pytest.fixture
async def event_engine() -> EventEngine:
    event_engine = EventEngine()
    await event_engine.startup()
    yield event_engine
    await event_engine.shutdown()
