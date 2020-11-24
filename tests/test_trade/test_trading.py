import pytest
import asyncio

from hq2redis import HQ2Redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.order import OrderRepository
from app.db.repositories.statement import StatementRepository
from app.models.domain.users import UserInDB
from app.models.enums import OrderStatusEnum
from app.models.schemas.orders import OrderInCreate
from app.services.engines.main_engine import MainEngine
from tests.json.order import order_in_create_json
from tests.mock.mock_load_entrust_orders import mock_load_entrust_orders

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
async def main_engine_with_mock(db: AsyncIOMotorDatabase, quotes_api: HQ2Redis, session_mocker):
    session_mocker.patch("app.services.engines.main_engine.MainEngine.load_entrust_orders", mock_load_entrust_orders)
    main_engine = MainEngine(db, quotes_api)
    await main_engine.startup()
    yield main_engine
    await main_engine.shutdown()


@pytest.fixture
def order_buy() -> OrderInCreate:
    return OrderInCreate(**order_in_create_json)


async def test_user_buy_stock(
    main_engine_with_mock: MainEngine,
    test_user_scope_func: UserInDB,
    db: AsyncIOMotorDatabase,
    order_buy: OrderInCreate,
):
    order = await main_engine_with_mock.on_order_arrived(order_buy, test_user_scope_func)
    await asyncio.sleep(2)
    order_after_trade = await OrderRepository(db).get_order_by_entrust_id(order.entrust_id)
    assert order_after_trade.status == OrderStatusEnum.ALL_FINISHED
    statement = await StatementRepository(db).get_statement_list_by_symbol(
        user_id=test_user_scope_func.id, symbol=order.symbol
    )
    print(order_after_trade)
