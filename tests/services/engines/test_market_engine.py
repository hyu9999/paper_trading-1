import asyncio

import pytest
from pytest_mock import MockerFixture
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.order import OrderRepository
from app.models.schemas.quotes import Quotes
from app.models.domain.orders import OrderInDB
from app.models.enums import OrderTypeEnum, OrderStatusEnum
from app.services.engines.main_engine import MainEngine
from tests.json.quotes import quotes_json

pytestmark = pytest.mark.asyncio


async def get_ticks(stock_code: str):
    quotes_json.update({"symbol": stock_code.split(".")[0]})
    quotes_json.update({"exchange": stock_code.split(".")[1]})
    return Quotes(**quotes_json)


@pytest.mark.parametrize(
    "order",
    [
        pytest.lazy_fixture("order_buy_type"),
        pytest.lazy_fixture("order_sell_type"),
        pytest.lazy_fixture("order_cancel_type"),
    ]
)
async def test_market_engine_can_matchmaking(
    main_engine: MainEngine,
    order: OrderInDB,
    mocker: MockerFixture,
    db: AsyncIOMotorDatabase
):
    mocker.patch("app.services.quotes.tdx.TDXQuotes.get_ticks", get_ticks)
    await main_engine.market_engine.put(order)
    await asyncio.sleep(2)
    if order.order_type == OrderTypeEnum.CANCEL:
        order_after_update = await OrderRepository(db).get_order_by_entrust_id(order.entrust_id)
        assert order_after_update.status == OrderStatusEnum.CANCELED
    elif order.order_type == OrderTypeEnum.LIQUIDATION:
        pass
    else:
        pass
