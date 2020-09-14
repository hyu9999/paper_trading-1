import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.domain.users import User

from app import settings
from app.db.repositories.users import UsersRepository


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


@pytest.fixture
async def test_user(db: AsyncIOMotorDatabase) -> User:
    return await UsersRepository(db).create_user(capital=10000000)
