import asyncio
from decimal import Decimal

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from pytest_mock import MockerFixture

from app.db.repositories.order import OrderRepository
from app.models.domain.orders import OrderInDB
from app.models.domain.statement import Costs
from app.models.enums import OrderStatusEnum, OrderTypeEnum
from app.services.engines.market_engine.base import BaseMarket

pytestmark = pytest.mark.asyncio


async def mock_create_position(*args, **kwargs):
    return Decimal("100"), Costs(commission="5", tax="0", total="5")


async def mock_reduce_position(*args, **kwargs):
    return Decimal("100"), Costs(commission="5", tax="5", total="10")


@pytest.mark.parametrize(
    "order_in_db",
    [
        pytest.lazy_fixture("order_buy_type"),
        pytest.lazy_fixture("order_sell_type"),
    ],
)
async def test_market_engine_can_matchmaking(
    market_engine: BaseMarket,
    order_in_db: OrderInDB,
    mocker: MockerFixture,
    db: AsyncIOMotorDatabase,
):
    mocker.patch(
        "app.services.engines.user_engine.UserEngine.create_position",
        mock_create_position,
    )
    mocker.patch(
        "app.services.engines.user_engine.UserEngine.reduce_position",
        mock_reduce_position,
    )
    await market_engine.put(order_in_db)
    await asyncio.sleep(2)
    order_after_update = await OrderRepository(db).get_order_by_id(order_in_db.id)
    if order_in_db.order_type == OrderTypeEnum.CANCEL:
        assert order_after_update.status == OrderStatusEnum.CANCELED
    else:
        assert order_after_update.status == OrderStatusEnum.ALL_FINISHED
