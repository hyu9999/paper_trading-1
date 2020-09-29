import asyncio

import pytest
from fastapi import FastAPI
from dynaconf import Dynaconf
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from app import settings as base_settings
from app.core import jwt
from app.db.repositories.order import OrderRepository
from app.db.repositories.user import UserRepository
from app.models.domain.users import UserInDB
from app.services.engines.main_engine import MainEngine
from app.services.engines.market_engine.base import BaseMarket
from app.services.quotes.tdx import TDXQuotes
from app.services.quotes.base import BaseQuotes
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import EventEngine
from tests.json.order import order_in_create_json

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
async def db(settings: Dynaconf) -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(
        settings.db.url, maxPoolSize=settings.db.max_connections, minPoolSize=settings.db.min_connections
    )
    yield client[settings.db.name]
    client.close()


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


@pytest.fixture
async def quotes_api() -> BaseQuotes:
    quotes_api = TDXQuotes()
    await quotes_api.connect_pool()
    yield quotes_api
    await quotes_api.close()


@pytest.fixture
async def user_engine(event_engine: EventEngine, db: AsyncIOMotorDatabase, quotes_api: BaseQuotes) -> UserEngine:
    user_engine = UserEngine(event_engine, db, quotes_api)
    await user_engine.startup()
    yield user_engine
    await user_engine.shutdown()


@pytest.fixture
async def market_engine(db: AsyncIOMotorDatabase) -> BaseMarket:
    main_engine = MainEngine(db)
    await main_engine.event_engine.startup()
    await main_engine.quotes_api.connect_pool()
    await main_engine.market_engine.startup()
    await main_engine.register_event()
    yield main_engine.market_engine
    await main_engine.market_engine.shutdown()
    await main_engine.quotes_api.close()
    await main_engine.event_engine.shutdown()


@pytest.fixture(scope="session")
async def main_engine(db: AsyncIOMotorDatabase):
    main_engine = MainEngine(db)
    await main_engine.startup()
    yield main_engine
    await main_engine.shutdown()


@pytest.fixture
async def order_buy_type(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {**order_in_create_json, **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000"}}
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_sell_type(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {**order_in_create_json, **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000",
                                       "order_type": "sell"}}
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_cancel_type(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {**order_in_create_json, **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000",
                                       "order_type": "cancel"}}
    return await OrderRepository(db).create_order(**json)
