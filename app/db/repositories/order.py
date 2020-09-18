from app import settings
from app.db.repositories.base import BaseRepository

from app.models.domain.orders import OrderInDB
from app.models.types import PyDecimal
from app.models.enums import ExchangeEnum, OrderTypeEnum, PriceTypeEnum, TradeTypeEnum


class OrderRepository(BaseRepository):
    COLLECTION_NAME = settings.db.collections.order

    async def create_order(
        self,
        *,
        symbol: str,
        exchange: ExchangeEnum,
        quantity: int,
        price: PyDecimal,
        order_type: OrderTypeEnum,
        price_type: PriceTypeEnum,
        trade_type: TradeTypeEnum,
    ) -> OrderInDB:
        order = OrderInDB(symbol=symbol, exchange=exchange, quantity=quantity, price=price, order_type=order_type,
                          price_type=price_type, trade_type=trade_type)
        order_row = await self.collection.insert_one(order.dict(exclude={"id"}))
        order.id = order_row.inserted_id
        return order

    async def update_order(
        self,
        *,
        symbol: str,
        exchange: ExchangeEnum,
        quantity: int,
        price: PyDecimal,
        order_type: OrderTypeEnum,
        price_type: PriceTypeEnum,
        trade_type: TradeTypeEnum,
    ):
        pass
