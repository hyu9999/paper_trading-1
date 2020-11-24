import copy

import pytest
import asyncio
from decimal import Decimal

from hq2redis import HQ2Redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.order import OrderRepository
from app.db.repositories.position import PositionRepository
from app.db.repositories.statement import StatementRepository
from app.db.repositories.user import UserRepository
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


@pytest.fixture
def order_sell() -> OrderInCreate:
    order_sell_json = copy.deepcopy(order_in_create_json)
    order_sell_json.update({"order_type": "sell"})
    order_sell_json.update({"price": "1"})
    return OrderInCreate(**order_sell_json)


async def test_user_buy(
    main_engine_with_mock: MainEngine,
    test_user_scope_func: UserInDB,
    db: AsyncIOMotorDatabase,
    order_buy: OrderInCreate,
):
    order = await main_engine_with_mock.on_order_arrived(order_buy, test_user_scope_func)
    await asyncio.sleep(2)
    # 订单
    order_after_trade = await OrderRepository(db).get_order_by_entrust_id(order.entrust_id)
    assert order_after_trade.status == OrderStatusEnum.ALL_FINISHED
    statement_list = await StatementRepository(db).get_statement_list_by_symbol(
        user_id=test_user_scope_func.id, symbol=order.symbol,
    )
    # 流水
    assert statement_list
    statement = statement_list[0]
    assert statement.volume == order_buy.volume
    assert statement.costs.tax.to_decimal() == Decimal(0)
    amount = order_buy.volume * statement.sold_price.to_decimal()
    assert statement.costs.commission.to_decimal() == amount * test_user_scope_func.commission.to_decimal()

    # 资产
    user_after_update = await UserRepository(db).get_user_by_id(test_user_scope_func.id)
    assert user_after_update.securities.to_decimal() == amount
    assert user_after_update.cash.to_decimal() == test_user_scope_func.cash.to_decimal() - amount - \
        amount * test_user_scope_func.commission.to_decimal()
    assert user_after_update.assets.to_decimal() == user_after_update.securities.to_decimal() + \
        user_after_update.cash.to_decimal()

    # 持仓
    position_after_update = await PositionRepository(db).get_positions_by_user_id(test_user_scope_func.id)
    assert position_after_update
    assert position_after_update[0].volume == order_buy.volume == position_after_update[0].available_volume


async def test_user_sell(
    main_engine_with_mock: MainEngine,
    test_user_scope_func: UserInDB,
    db: AsyncIOMotorDatabase,
    order_sell: OrderInCreate,
    order_buy: OrderInCreate
):
    await main_engine_with_mock.on_order_arrived(order_buy, test_user_scope_func)
    await asyncio.sleep(3)
    user_after_buy = await UserRepository(db).get_user_by_id(test_user_scope_func.id)
    order = await main_engine_with_mock.on_order_arrived(order_sell, test_user_scope_func)
    await asyncio.sleep(3)
    # 订单
    order_after_trade = await OrderRepository(db).get_order_by_entrust_id(order.entrust_id)
    assert order_after_trade.status == OrderStatusEnum.ALL_FINISHED

    # 流水
    statement_list = await StatementRepository(db).get_statement_list_by_symbol(
        user_id=test_user_scope_func.id, symbol=order.symbol
    )
    statement = [s for s in statement_list if s.trade_category.value == "sell"][0]
    assert statement.volume == order_sell.volume
    amount = order.volume * statement.sold_price.to_decimal()
    assert statement.costs.tax.to_decimal() == amount * test_user_scope_func.tax_rate.to_decimal()
    assert statement.costs.commission.to_decimal() == amount * test_user_scope_func.commission.to_decimal()
    assert statement.costs.total.to_decimal() == \
        statement.costs.tax.to_decimal() + statement.costs.commission.to_decimal()

    # 资产
    user_after_update = await UserRepository(db).get_user_by_id(test_user_scope_func.id)
    assert user_after_update.securities.to_decimal() == Decimal("0")
    assert user_after_update.cash.to_decimal() == user_after_buy.cash.to_decimal() + amount - \
        statement.costs.total.to_decimal()
    assert user_after_update.assets.to_decimal() == user_after_update.securities.to_decimal() + \
        user_after_update.cash.to_decimal()

    # 持仓
    position_after_update = await PositionRepository(db).get_positions_by_user_id(test_user_scope_func.id)
    assert not position_after_update
