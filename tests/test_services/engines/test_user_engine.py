import asyncio
from decimal import Decimal
from typing import Optional

import pytest
from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorDatabase
from pytest_mock import MockerFixture

from app.db.repositories.order import OrderRepository
from app.db.repositories.position import PositionRepository
from app.exceptions.service import (
    InsufficientFunds,
    NoPositionsAvailable,
    NotEnoughAvailablePositions,
)
from app.models.domain.orders import OrderInDB
from app.models.domain.position import PositionInDB
from app.models.domain.statement import Costs
from app.models.domain.users import UserInDB
from app.models.enums import OrderTypeEnum
from app.models.schemas.orders import OrderInCreate
from app.models.schemas.position import PositionInCreate
from app.models.types import PyDecimal
from app.services.engines.user_engine import UserEngine
from tests.json.order import order_in_create_json
from tests.json.position import position_in_create_json
from tests.json.quotes import quotes_json

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
    order_in_create_json_buy_price_0 = {
        **order_in_create_json,
        **{"volume": "10000", "price": "100000"},
    }
    return OrderInCreate(**order_in_create_json_buy_price_0)


@pytest.fixture
async def order_create_with_sell():
    order_in_create_json_sell = {**order_in_create_json, **{"order_type": "sell"}}
    return OrderInCreate(**order_in_create_json_sell)


@pytest.fixture
async def order_t0(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{
            "user_id": test_user_scope_func.id,
            "price_type": "market",
            "amount": "1000",
            "sold_price": "10",
            "frozen_amount": PyDecimal("10"),
        },
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_t1(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{
            "user_id": test_user_scope_func.id,
            "price_type": "market",
            "amount": "1000",
            "trade_type": "T1",
            "sold_price": "10",
            "frozen_amount": PyDecimal("10"),
        },
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_sell_90(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{
            "user_id": test_user_scope_func.id,
            "price_type": "market",
            "order_type": "sell",
            "volume": "90",
            "amount": "900",
            "sold_price": "10",
            "frozen_stock_volume": 90,
        },
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_sell_100(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{
            "user_id": test_user_scope_func.id,
            "price_type": "market",
            "order_type": "sell",
            "volume": "100",
            "amount": "900",
            "sold_price": "10",
            "frozen_stock_volume": 100,
        },
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def position_in_create_diff_stock(
    db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB
):
    json = {
        **position_in_create_json,
        **{"user": test_user_scope_func.id, "symbol": "601817"},
    }
    return await PositionRepository(db).create_position(
        **PositionInCreate(**json).dict()
    )


@pytest.fixture
async def position_in_create_no_available(
    db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB
):
    json = {**position_in_create_json, **{"user": test_user_scope_func.id}}
    return await PositionRepository(db).create_position(
        **PositionInCreate(**json).dict()
    )


@pytest.fixture
async def position_in_create_available_100(
    db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB
):
    json = {
        **position_in_create_json,
        **{"user": test_user_scope_func.id, "available_volume": 100},
    }
    return await PositionRepository(db).create_position(
        **PositionInCreate(**json).dict()
    )


@pytest.fixture
async def position_in_create_available_10000(
    db: AsyncIOMotorDatabase, test_user_scope_func: UserInDB
):
    json = {
        **position_in_create_json,
        **{"user": test_user_scope_func.id, "available_volume": 10000},
    }
    return await PositionRepository(db).create_position(
        **PositionInCreate(**json).dict()
    )


async def mock_update_user(*args, **kwargs):
    pass


@pytest.mark.parametrize(
    "order_in_create, is_exception",
    [
        (pytest.lazy_fixture("order_create_with_buy"), False),
        (pytest.lazy_fixture("order_create_with_buy_no_price"), False),
        (pytest.lazy_fixture("order_create_with_buy_big_amount"), True),
    ],
)
async def test_can_frozen_user_cash(
    test_user_scope_func: UserInDB,
    user_engine: UserEngine,
    order_in_create: OrderInCreate,
    is_exception: bool,
):
    """测试提交买单时是否能正确冻结用户可用现金.

    测试对象为: UserEngine.__capital_validation.
    """
    is_caught = False
    try:
        frozen_cash = await user_engine.pre_trade_validation(
            order_in_create, test_user_scope_func
        )
        await asyncio.sleep(1)
    except InsufficientFunds:
        is_caught = True
    else:
        user_after_task = await user_engine.user_repo.get_user_by_id(
            test_user_scope_func.id
        )
        # 订单拟定交易额
        amount = (
            Decimal(order_in_create.volume)
            * order_in_create.price.to_decimal()
            * (1 + test_user_scope_func.commission.to_decimal())
        )
        # 判断冻结金额是否正确
        assert frozen_cash == amount
        # 判断用户的现金是否被正确冻结
        assert user_after_task.cash == PyDecimal(
            test_user_scope_func.cash.to_decimal() - amount
        )
    finally:
        assert is_caught == is_exception


@pytest.mark.parametrize(
    "order_in_create, expected_exception, position",
    [
        (
            pytest.lazy_fixture("order_create_with_sell"),
            NoPositionsAvailable,
            pytest.lazy_fixture("position_in_create_diff_stock"),
        ),
        (
            pytest.lazy_fixture("order_create_with_sell"),
            NotEnoughAvailablePositions,
            pytest.lazy_fixture("position_in_create_no_available"),
        ),
        (
            pytest.lazy_fixture("order_create_with_sell"),
            None,
            pytest.lazy_fixture("position_in_create_available_10000"),
        ),
    ],
)
async def test_can_frozen_user_position(
    user_engine: UserEngine,
    order_in_create: OrderInCreate,
    expected_exception: Optional[Exception],
    position: PositionInDB,
):
    """测试提交卖单时是否能正确冻结账户可用仓位.

    测试对象为: UserEngine.__position_validation.
    """
    user = await user_engine.user_repo.get_user_by_id(position.user)
    exception = None
    try:
        await user_engine.pre_trade_validation(order_in_create, user)
        await asyncio.sleep(1)
    except NoPositionsAvailable:
        exception = NoPositionsAvailable
    except NotEnoughAvailablePositions:
        exception = NotEnoughAvailablePositions
    else:
        position_after_update = await user_engine.position_repo.get_position_by_id(
            position.id
        )
        assert (
            position_after_update.available_volume
            == position.available_volume - order_in_create.volume
        )
    finally:
        assert exception == expected_exception


@pytest.mark.parametrize(
    "order_in_db", [pytest.lazy_fixture("order_t0"), pytest.lazy_fixture("order_t1")]
)
async def test_can_create_position(
    user_engine: UserEngine, order_in_db: OrderInDB, mocker: MockerFixture
):
    """测试能否正确新建持仓."""
    mocker.patch(
        "app.services.engines.user_engine.UserEngine.update_user", mock_update_user
    )
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    position = await user_engine.position_repo.get_position(
        order_in_db.user, order_in_db.symbol, order_in_db.exchange
    )
    if order_in_db.trade_type.value == "TO":
        assert position.available_volume == order_in_db.traded_volume
    else:
        assert position.available_volume == 0


@pytest.mark.parametrize(
    "order_in_db", [pytest.lazy_fixture("order_t0"), pytest.lazy_fixture("order_t1")]
)
async def test_can_add_position(
    user_engine: UserEngine, order_in_db: OrderInDB, mocker: MockerFixture
):
    """测试能否正确加仓."""
    mocker.patch(
        "app.services.engines.user_engine.UserEngine.update_user", mock_update_user
    )
    order_in_db.sold_price = order_in_db.price
    order_in_db.traded_volume = order_in_db.volume
    # 建仓
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    # 加仓
    await user_engine.create_position(order_in_db)
    await asyncio.sleep(1)
    position = await user_engine.position_repo.get_position(
        order_in_db.user, order_in_db.symbol, order_in_db.exchange
    )
    assert position.volume == 2 * order_in_db.traded_volume
    assert position.cost == order_in_db.sold_price
    if order_in_db.trade_type.value == "T1":
        assert position.available_volume == 0
    else:
        assert position.available_volume == 2 * order_in_db.traded_volume


@pytest.mark.parametrize(
    "order_sell",
    [pytest.lazy_fixture("order_sell_90"), pytest.lazy_fixture("order_sell_100")],
)
async def test_can_reduce_position(
    user_engine: UserEngine,
    mocker: MockerFixture,
    position_in_create_available_100: PositionInDB,
    order_sell: OrderInDB,
):
    """测试能否正确减仓."""
    mocker.patch(
        "app.services.engines.user_engine.UserEngine.update_user", mock_update_user
    )
    order_sell.traded_volume = order_sell.volume
    await user_engine.reduce_position(order_sell)
    await asyncio.sleep(1)
    position_after_task = await user_engine.position_repo.get_position_by_id(
        position_in_create_available_100.id
    )
    assert (
        position_after_task.volume
        == position_in_create_available_100.volume - order_sell.volume
    )
    if position_after_task.volume == 0:
        assert position_after_task.last_sell_date


@pytest.mark.parametrize(
    "order, securities",
    [
        (pytest.lazy_fixture("order_t0"), PyDecimal("100.00")),
        (pytest.lazy_fixture("order_sell_90"), PyDecimal("0")),
    ],
)
async def test_can_update_user(
    user_engine: UserEngine, order: OrderInDB, securities: Decimal128
):
    """测试更新用户数据."""
    await user_engine.update_user(
        order, Decimal(100), Costs(commission="5", total="5", tax="0")
    )
    await asyncio.sleep(1)
    user_after_task = await user_engine.user_repo.get_user_by_id(order.user)
    assert user_after_task.securities == securities


@pytest.mark.parametrize(
    "order, position",
    [
        (pytest.lazy_fixture("order_t0"), None),
        (
            pytest.lazy_fixture("order_sell_90"),
            pytest.lazy_fixture("position_in_create_available_100"),
        ),
    ],
)
async def test_can_unfreeze_user_assets(
    user_engine: UserEngine,
    order: OrderInDB,
    position: PositionInDB,
):
    """测试解冻用户资产."""
    user_before_task = await user_engine.user_repo.get_user_by_id(order.user)
    await user_engine.process_unfreeze(order)
    await asyncio.sleep(2)
    if order.order_type == OrderTypeEnum.BUY:
        user_after_task = await user_engine.user_repo.get_user_by_id(order.user)
        assert (
            user_after_task.cash.to_decimal()
            == user_before_task.cash.to_decimal() + order.frozen_amount.to_decimal()
        )
    else:
        position_after_task = await user_engine.position_repo.get_position_by_id(
            position.id
        )
        assert (
            position_after_task.available_volume
            == position.available_volume + order.frozen_stock_volume
        )


async def test_can_liquidate_user_position(
    user_engine: UserEngine,
    test_user_scope_func: UserInDB,
    position_in_create_available_100: PositionInDB,
):
    await user_engine.liquidate_user_position(test_user_scope_func)
    await asyncio.sleep(1)
    position_after_task = await user_engine.position_repo.get_position_by_id(
        position_in_create_available_100.id
    )
    assert str(position_after_task.current_price) == str(quotes_json["ask1_p"])
