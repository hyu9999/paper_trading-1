import asyncio
from decimal import Decimal

import pytest
from pytest_mock import MockerFixture
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.order import OrderRepository
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCreate
from app.models.enums import PriceTypeEnum, OrderStatusEnum
from app.services.engines.main_engine import MainEngine
from tests.json.order import order_in_create_json

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def order_submitting_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "提交中"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_not_done_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "未成交"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_part_finished_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "部分成交"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_all_finished_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "全部成交"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_cancel_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "已撤销"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_reject_status(test_user_scope_func: UserInDB, db: AsyncIOMotorDatabase):
    json = {
        **order_in_create_json,
        **{"user_id": test_user_scope_func.id, "price_type": "market", "amount": "1000", "status": "已拒单"}
    }
    return await OrderRepository(db).create_order(**json)


@pytest.fixture
async def order_list(
    order_submitting_status: OrderInDB,
    order_not_done_status: OrderInDB,
    order_part_finished_status: OrderInDB,
    order_all_finished_status: OrderInDB,
    order_cancel_status: OrderInDB,
    order_reject_status: OrderInDB,
) -> set:
    return {order_submitting_status.id, order_not_done_status.id, order_part_finished_status.id,
            order_all_finished_status.id, order_cancel_status.id, order_reject_status.id}

entrust_orders = set()


async def mock_put_entrust_order(self, order: OrderInDB, *args, **kwargs):
    entrust_orders.add(order.id)


async def mock_pre_trade_validation(*args, **kwargs):
    return Decimal(1000)


async def test_main_engine_can_load_entrust_orders(
    main_engine: MainEngine,
    mocker: MockerFixture,
    order_list: set
):
    mocker.patch("app.services.engines.market_engine.china_a_market.ChinaAMarket.put", mock_put_entrust_order)
    await main_engine.load_entrust_orders()
    assert len(entrust_orders.intersection(order_list)) == 2


@pytest.mark.parametrize(
    "json, expect_price_type",
    [
        (order_in_create_json, PriceTypeEnum.LIMIT),
        ({**order_in_create_json, **{"price": "0"}}, PriceTypeEnum.MARKET),
    ]
)
async def test_main_engine_on_order_arrived(
    main_engine: MainEngine,
    mocker: MockerFixture,
    test_user_scope_func: UserInDB,
    db: AsyncIOMotorDatabase,
    json: dict,
    expect_price_type: PriceTypeEnum
):
    mocker.patch("app.services.engines.user_engine.UserEngine.pre_trade_validation", mock_pre_trade_validation)
    mocker.patch("app.services.engines.market_engine.china_a_market.ChinaAMarket.put", mock_put_entrust_order)
    order = await main_engine.on_order_arrived(OrderInCreate(**json), test_user_scope_func)
    await asyncio.sleep(1)
    order_after_create = await OrderRepository(db).get_order_by_entrust_id(order.entrust_id)
    assert order_after_create
    assert order_after_create.price_type == expect_price_type


async def test_main_engine_can_refuse_order(
    main_engine: MainEngine,
    order_not_done_status: OrderInDB,
    db: AsyncIOMotorDatabase,
):
    await main_engine.refuse_order(order_not_done_status)
    await asyncio.sleep(1)
    order_after_create = await OrderRepository(db).get_order_by_entrust_id(order_not_done_status.entrust_id)
    assert order_after_create.status == OrderStatusEnum.REJECTED
