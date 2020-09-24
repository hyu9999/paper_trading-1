from typing import Type
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.repositories.order import OrderRepository
from app.models.base import PyObjectId
from app.models.enums import PriceTypeEnum
from app.models.domain.users import UserInDB
from app.models.schemas.event_payload import (
    OrderInCreatePayload,
    OrderInUpdatePayload,
    OrderInUpdateStatusPayload
)
from app.models.schemas.orders import OrderInCreate, OrderInCreateViewResponse
from app.services.engines.base import BaseEngine
from app.services.engines.log_engine import LogEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.user_engine import UserEngine, Event
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from app.services.engines.event_constants import (
    ORDER_CREATE_EVENT,
    ORDER_UPDATE_EVENT,
)


class MainEngine(BaseEngine):
    def __init__(
        self,
        db: AsyncIOMotorClient,
        event_engine: Type[EventEngine] = None
    ) -> None:
        self.event_engine = event_engine() if event_engine else EventEngine()
        self.db = db
        self.log_engine = LogEngine(self.event_engine)
        self.order_repo = OrderRepository(db[settings.db.name])
        self.user_engine = UserEngine(self.event_engine, self.db)
        self.market_engine = MARKET_NAME_MAPPING[settings.service.market](
            self.event_engine
        )

    def startup(self) -> None:
        self.event_engine.startup()
        self.log_engine.startup()
        self.user_engine.startup()
        self.market_engine.startup()
        self.register_event()

    def shutdown(self) -> None:
        self.market_engine.shutdown()
        self.user_engine.shutdown()
        self.log_engine.shutdown()
        self.event_engine.shutdown()

    def register_event(self) -> None:
        self.event_engine.register(ORDER_CREATE_EVENT, self.process_order_create)
        self.event_engine.register(ORDER_UPDATE_EVENT, self.process_order_update)

    def process_order_create(self, payload: OrderInCreatePayload) -> None:
        self.order_repo.process_create_order(payload)

    def process_order_update(self, payload: OrderInUpdatePayload) -> None:
        self.order_repo.process_update_order(payload)

    def process_order_status_update(self, payload: OrderInUpdateStatusPayload) -> None:
        self.order_repo.process_update_order_status(payload)

    async def on_order_arrived(self, order: OrderInCreate, user: UserInDB) -> OrderInCreateViewResponse:
        """新订单到达."""
        await self.user_engine.pre_trade_validation(order, user)
        # 根据订单的股票价格确定价格类型
        order.price_type = PriceTypeEnum.MARKET if str(order.price) == "0" else PriceTypeEnum.LIMIT
        order_in_db = OrderInCreatePayload(**dict(order), user=user.id, order_date=datetime.utcnow(),
                                           order_id=PyObjectId())
        order_create_event = Event(ORDER_CREATE_EVENT, order_in_db)
        self.event_engine.put(order_create_event)
        self.market_engine.put_order(order_in_db)
        return OrderInCreateViewResponse(**dict(order_in_db))
