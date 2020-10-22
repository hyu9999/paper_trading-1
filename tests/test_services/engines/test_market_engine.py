import asyncio

import pytest
from pytest_mock import MockerFixture
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings
from app.db.repositories.order import OrderRepository
from app.models.schemas.quotes import Quotes
from app.models.domain.orders import OrderInDB
from app.models.enums import OrderTypeEnum, OrderStatusEnum
from app.services.engines.market_engine.base import BaseMarket
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from tests.json.quotes import quotes_json

pytestmark = pytest.mark.asyncio


async def mock_get_ticks(self, stock_code: str):
    quotes_json.update({"symbol": stock_code.split(".")[0]})
    quotes_json.update({"exchange": stock_code.split(".")[1]})
    return Quotes(**quotes_json)


async def mock_create_position(*args, **kwargs):
    pass


async def mock_reduce_position(*args, **kwargs):
    pass


def is_skip(*args):
    market_class = MARKET_NAME_MAPPING[settings.service.market]
    return market_class.is_trading_time()


@pytest.mark.skipif(is_skip, reason="非交易时间无法测试.")
@pytest.mark.parametrize(
    "order_in_db",
    [
        pytest.lazy_fixture("order_buy_type"),
        pytest.lazy_fixture("order_sell_type"),
        pytest.lazy_fixture("order_cancel_type"),
    ]
)
async def test_market_engine_can_matchmaking(
    market_engine: BaseMarket,
    order_in_db: OrderInDB,
    mocker: MockerFixture,
    db: AsyncIOMotorDatabase
):
    mocker.patch("app.services.engines.user_engine.UserEngine.create_position", mock_create_position)
    mocker.patch("app.services.engines.user_engine.UserEngine.reduce_position", mock_reduce_position)
    await market_engine.put(order_in_db)
    await asyncio.sleep(1)
    order_after_update = await OrderRepository(db).get_order_by_id(order_in_db.id)
    if order_in_db.order_type == OrderTypeEnum.CANCEL:
        assert order_after_update.status == OrderStatusEnum.CANCELED
    else:
        assert order_after_update.status == OrderStatusEnum.ALL_FINISHED
