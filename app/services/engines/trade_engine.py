from typing import Type
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.repositories.order import OrderRepository
from app.models.base import PyObjectId
from app.models.enums import PriceTypeEnum
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCreate, OrderInCreateResponse
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.user_engine import UserEngine, Event
from app.services.engines.event_constants import ORDER_CREATE_EVENT


class TradeEngine(BaseEngine):
    def __init__(self, db: AsyncIOMotorClient, event_engine: Type[EventEngine] = None) -> None:
        self.event_engine = event_engine() if event_engine else EventEngine()
        self.db = db
        self.order_repo = OrderRepository(db[settings.db.name])
        self.user_engine = UserEngine(self.event_engine, self.db)

    async def startup(self) -> None:
        await self.event_engine.startup()
        await self.register_event()
        await self.user_engine.startup()

    async def shutdown(self) -> None:
        await self.event_engine.shutdown()
        await self.user_engine.shutdown()

    async def register_event(self) -> None:
        await self.event_engine.register(ORDER_CREATE_EVENT, self.process_order_create)

    def process_order_create(self, event: Event) -> None:
        self.order_repo.process_create_order(event.data)

    async def on_order_arrived(self, order: OrderInCreate, user: UserInDB) -> OrderInCreateResponse:
        """新订单到达."""
        await self.user_engine.pre_trade_validation(order, user)
        # 根据订单的股票价格确定价格类型
        order.price_type = PriceTypeEnum.MARKET if str(order.price) == "0" else PriceTypeEnum.LIMIT
        order_in_db = OrderInDB(**dict(order), user=user.id, order_date=datetime.utcnow(), order_id=PyObjectId())
        order_create_event = Event(ORDER_CREATE_EVENT, order_in_db)
        await self.event_engine.put(order_create_event)
        return OrderInCreateResponse(**dict(order_in_db))
