import pytest
from asgi_lifespan import LifespanManager
from dynaconf import Dynaconf
from fastapi import FastAPI
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

from app import settings as base_settings
from app.core import jwt
from app.db.repositories.user import UserRepository
from app.models.domain.users import UserInDB
from app.models.schemas.users import UserInCreate


@pytest.fixture(scope="session")
def settings() -> Dynaconf:
    base_settings.setenv("testing")
    return base_settings


@pytest.fixture
async def db(settings: Dynaconf) -> Database:
    client = AsyncIOMotorClient(
        settings.db.url,
        maxPoolSize=settings.db.max_connections,
        minPoolSize=settings.db.min_connections,
    )
    yield client.get_database(settings.MONGO_DB)
    await client.drop_database(settings.MONGO_DB)
    client.close()


@pytest.fixture
def app() -> FastAPI:
    from app.main import get_application

    return get_application()


@pytest.fixture
async def initialized_app(app: FastAPI) -> FastAPI:
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(db: Database, app: FastAPI) -> AsyncClient:
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"},
        ) as client:
            yield client


@pytest.fixture
async def test_user(db: Database) -> UserInDB:
    user_in_create = UserInCreate(capital=10000000)
    return await UserRepository(db).create_user(user_in_create)


@pytest.fixture
def token(test_user: UserInDB, settings: Dynaconf) -> str:
    if settings.auth_mode == "JWT":
        return jwt.create_access_token_for_user(test_user.id)
    elif settings.auth_mode == "UID":
        return str(test_user.id)
    else:
        raise ValueError("请设置可用的认证模式.")


@pytest.fixture
def authorized_client(
    client: AsyncClient, token: str, settings: Dynaconf
) -> AsyncClient:
    client.headers = {
        "Authorization": f"{settings.token_prefix} {token}",
        **client.headers,
    }
    return client
