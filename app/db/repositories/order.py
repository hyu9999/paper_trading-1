from app import settings
from app.db.repositories.base import BaseRepository
from app.models.types import PyDecimal
from app.models.domain.orders import OrderInDB
from app.models.schemas.event_payload import (
    OrderInCreatePayload,
    OrderInUpdatePayload,
    OrderInUpdateStatusPayload
)
from app.models.enums import ExchangeEnum, OrderTypeEnum, PriceTypeEnum, TradeTypeEnum


class OrderRepository(BaseRepository):
    """订单仓库相关方法.

    函数名称以process开头的为事件处理专用函数.
    """
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
    ) -> None:
        pass

    def process_create_order(self, order: OrderInCreatePayload) -> None:
        self.collection.insert_one(order.dict(exclude={"id"}))

    def process_update_order(self, order: OrderInUpdatePayload) -> None:
        self.collection.update_one({"order_id": order.order_id}, {"$set": order.dict(exclude={"order_id"})})

    def process_update_order_status(self, order: OrderInUpdateStatusPayload) -> None:
        self.collection.update_one({"_id": order.id}, {"$set": {"status": order.status}})
