from app import settings
from app.db.repositories.base import BaseRepository

from app.models.domain.orders import OrderInDB
from app.models.types import PyDecimal, PyObjectId
from app.models.schemas.orders import OrderInCreate
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
    ):
        pass

    def process_create_order(self, order: OrderInDB) -> None:
        self.collection.insert_one(order.dict(exclude={"id"}))
