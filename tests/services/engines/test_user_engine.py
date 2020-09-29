import asyncio
from typing import Optional
from decimal import Decimal
from datetime import datetime

import pytest
from pytest_mock import MockerFixture
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.order import OrderRepository
from app.db.repositories.position import PositionRepository
from app.exceptions.service import InsufficientFunds, NoPositionsAvailable, NotEnoughAvailablePositions
from app.models.types import PyDecimal
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCreate
from app.models.domain.position import PositionInDB
from app.models.schemas.position import PositionInCreate
from app.services.engines.user_engine import UserEngine
from tests.json.order import order_in_create_json

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def order_create_with_buy():
    return OrderInCreate(**order_in_create_json)


@pytest.fixture
async def order_create_with_buy_no_price():
    order_in_create_json_buy_price_0 = {**order_in_create_json, **{"price": "0"}}
    return OrderInCreate(**order_in_create_json_buy_price_0)


@pytest.fixture
async def order_create_with_buy_big_amount():
    order_in_create_json_buy_price_0 = {**order_in_create_json, **{"quantity": "10000", "price": "100000"}}
    return OrderInCreate(**order_in_create_json_buy_price_0)


@pytest.fixture
async def order_create_with_sell():
    order_in_create_json_sell = {**order_in_create_json, **{"order_type": "sell"}}
    return OrderInCreate(**order_in_create_json_sell)


@pytest.fixture
async def order_t0(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {**order_in_create_json, **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000"}}
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_t1(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {**order_in_create_json,
            **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "trade_type": "T1"}}
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_sell_90(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "order_type": "sell", "quantity": "10",
           "amount": "900"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_sell_100(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "order_type": "sell", "quantity": "10",
           "amount": "900"}
    }
    return await OrderRepository(db).create_order(**json)


position_in_create_json = {
    "symbol": "601816",
    "exchange": "SH",
    "quantity": 100,
    "available_quantity": 0,
    "cost": "10",
    "current_price": "10",
    "profit": "0",
    "first_buy_date": datetime.utcnow()
}


@pytest.fixture
async def position_in_create_diff_stock(db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB):
    json = {**position_in_create_json, **{"user": test_user_scope_func.id, "symbol": "601817"}}
    return await PositionRepository(db).create_position(**PositionInCreate(**json).dict())


@pytest.fixture
async def position_in_create_no_available(db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB):
    json = {**position_in_create_json, **{"user": test_user_scope_func.id}}
    return await PositionRepository(db).create_position(**PositionInCreate(**json).dict())


@pytest.fixture
async def position_in_create_available_100(db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB):
    json = {**position_in_create_json, **{"user": test_user_scope_func.id, "available_quantity": 100}}
    return await PositionRepository(db).create_position(**PositionInCreate(**json).dict())


async def mock_update_user(*args, **kwargs):
    pass


@pytest.mark.parametrize(
    "order_in_create, is_exception",
    [
        (pytest.lazy_fixture("order_create_with_buy"), False),
        (pytest.lazy_fixture("order_create_with_buy_no_price"), False),
        (pytest.lazy_fixture("order_create_with_buy_big_amount"), True)
    ],
)
async def test_can_frozen_user_cash(
    test_user_scope_func: UserInDB,
    user_engine: UserEngine,
    order_in_create: OrderInCreate,
    is_exception: bool
):
    """测试提交买单时是否能正确冻结用户可用现金.

    测试对象为: UserEngine.__capital_validation.
    """
    is_caught = False
    try:
        frozen_cash = await user_engine.pre_trade_validation(order_in_create, test_user_scope_func)
        await asyncio.sleep(1)
    except InsufficientFunds:
        is_caught = True
    else:
        user_after_task = await user_engine.user_repo.get_user_by_id(test_user_scope_func.id)
        # 订单拟定交易额
        amount = Decimal(order_in_create.quantity) * \
            order_in_create.price.to_decimal() * (1 + test_user_scope_func.commission.to_decimal())
        # 判断冻结金额是否正确
        assert frozen_cash == PyDecimal(test_user_scope_func.cash.to_decimal() - amount)
        # 判断用户的现金是否被正确冻结
        assert user_after_task.cash == frozen_cash
    finally:
        assert is_caught == is_exception


@pytest.mark.parametrize(
    "order_in_create, expected_exception, position_in_create",
    [
        (
            pytest.lazy_fixture("order_create_with_sell"),
            NoPositionsAvailable,
            pytest.lazy_fixture("position_in_create_diff_stock")
        ),
        (
            pytest.lazy_fixture("order_create_with_sell"),
            NotEnoughAvailablePositions,
            pytest.lazy_fixture("position_in_create_no_available")
        ),
        (
            pytest.lazy_fixture("order_create_with_sell"),
            None,
            pytest.lazy_fixture("position_in_create_available_100")
        ),
    ],
)
async def test_can_frozen_user_position(
    user_engine: UserEngine,
    order_in_create: OrderInCreate,
    expected_exception: Optional[Exception],
    position_in_create: PositionInDB
):
    """测试提交卖单时是否能正确冻结账户可用仓位.

    测试对象为: UserEngine.__position_validation.
    """
    user = await user_engine.user_repo.get_user_by_id(position_in_create.user)
    exception = None
    try:
        await user_engine.pre_trade_validation(order_in_create, user)
        await asyncio.sleep(1)
    except NoPositionsAvailable:
        exception = NoPositionsAvailable
    except NotEnoughAvailablePositions:
        exception = NotEnoughAvailablePositions
    else:
        position = await user_engine.position_repo.get_position_by_id(position_in_create.id)
        assert position.available_quantity == position_in_create.available_quantity - order_in_create.quantity
    finally:
        assert exception == expected_exception


@pytest.mark.parametrize(
    "order_in_db",
    [
        pytest.lazy_fixture("order_t0"),
        pytest.lazy_fixture("order_t1")
    ]
)
async def test_can_create_position(
    user_engine: UserEngine,
    order_in_db: OrderInDB,
    mocker: MockerFixture
):
    """测试能否正确新建持仓."""
    mocker.patch("app.services.engines.user_engine.UserEngine.update_user", mock_update_user)
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    position = await user_engine.position_repo.get_position(order_in_db.user, order_in_db.symbol, order_in_db.exchange)
    if order_in_db.trade_type.value == "TO":
        assert position.available_quantity == order_in_db.traded_quantity
    else:
        assert position.available_quantity == 0


@pytest.mark.parametrize(
    "order_in_db",
    [
        pytest.lazy_fixture("order_t0"),
        pytest.lazy_fixture("order_t1")
    ]
)
async def test_can_add_position(
    user_engine: UserEngine,
    order_in_db: OrderInDB,
    mocker: MockerFixture
):
    """测试能否正确加仓."""
    mocker.patch("app.services.engines.user_engine.UserEngine.update_user", mock_update_user)
    order_in_db.trade_price = order_in_db.price
    order_in_db.traded_quantity = order_in_db.quantity
    # 建仓
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    # 加仓
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    position = await user_engine.position_repo.get_position(order_in_db.user, order_in_db.symbol, order_in_db.exchange)
    assert position.quantity == 2 * order_in_db.traded_quantity
    assert position.cost == order_in_db.trade_price
    if order_in_db.trade_type.value == "T1":
        assert position.available_quantity == 0
    else:
        assert position.available_quantity == 2 * order_in_db.traded_quantity


@pytest.mark.parametrize(
    "order_sell",
    [
        pytest.lazy_fixture("order_sell_90"),
        pytest.lazy_fixture("order_sell_100")
    ]
)
async def test_can_reduce_position(
    user_engine: UserEngine,
    mocker: MockerFixture,
    position_in_create_available_100: PositionInDB,
    order_sell: OrderInDB,
):
    """测试能否正确减仓."""
    mocker.patch("app.services.engines.user_engine.UserEngine.update_user", mock_update_user)
    order_sell.traded_quantity = order_sell.quantity
    await user_engine.reduce_position(order_sell)
    await asyncio.sleep(1)
    position_after_task = await user_engine.position_repo.get_position_by_id(position_in_create_available_100.id)
    assert position_after_task.quantity == position_in_create_available_100.quantity - order_sell.quantity
    if position_after_task.quantity == 0:
        assert position_after_task.last_sell_date


@pytest.mark.parametrize(
    "order",
    [
        pytest.lazy_fixture("order_t0"),
        pytest.lazy_fixture("order_sell_90"),
    ]
)
async def test_can_update_user(
    user_engine: UserEngine,
    order: OrderInDB,
):
    """测试更新用户数据"""
    await user_engine.update_user(order, Decimal(100))
    await asyncio.sleep(1)
    user_after_task = await user_engine.user_repo.get_user_by_id(order.user)
    assert user_after_task.securities == PyDecimal("100.00")
