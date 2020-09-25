from typing import List
from datetime import date, datetime

from app import settings
from app.db.repositories.base import BaseRepository
from app.exceptions.db import EntityDoesNotExist
from app.models.domain.orders import OrderInDB
from app.models.types import PyDecimal, PyObjectId
from app.models.schemas.orders import OrderInUpdate, OrderInUpdateStatus
from app.models.enums import ExchangeEnum, OrderTypeEnum, PriceTypeEnum, TradeTypeEnum, OrderStatusEnum


class OrderRepository(BaseRepository):
    """订单仓库相关方法.

    函数名称以process开头的为事件处理专用函数.

    Raises
    ------
    EntityDoesNotExist
        订单不存在时触发
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

    async def get_order_by_order_id(self, order_id: PyObjectId) -> OrderInDB:
        order_row = await self.collection.find_one({"order_id": order_id})
        if order_row:
            return OrderInDB(**order_row)
        raise EntityDoesNotExist(f"订单`{order_id}`不存在.")

    async def get_orders(
        self,
        user_id: PyObjectId = None,
        status: List[OrderStatusEnum] = None,
        start_date: date = None,
        end_date: date = None,
    ) -> List[OrderInDB]:
        query = {
            "user_id": user_id,
            "status": {"$in": [s.value for s in status if s]},
        }
        if start_date:
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_date = datetime.combine(end_date, datetime.max.time())
        if not (start_date or end_date):
            date_query = None
        elif start_date and end_date:
            date_query = {
                "$gte": start_date,
                "$lt": end_date
            }
        elif start_date and not end_date:
            date_query = {
                "$gte": start_date
            }
        else:
            date_query = {
                "$lte": end_date
            }
        if date_query:
            query.update({"order_date": date_query})
        order_rows = self.collection.find(query)
        return [OrderInDB(**order) async for order in order_rows]

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

    async def process_create_order(self, order: OrderInDB) -> None:
        await self.collection.insert_one(order.dict(exclude={"id"}))

    async def process_update_order(self, order: OrderInUpdate) -> None:
        await self.collection.update_one({"order_id": order.order_id}, {"$set": order.dict(exclude={"order_id"})})

    async def process_update_order_status(self, order: OrderInUpdateStatus) -> None:
        await self.collection.update_one({"order_id": order.order_id}, {"$set": {"status": order.status}})
