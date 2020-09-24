from typing import Type
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.repositories.order import OrderRepository
from app.models.base import PyObjectId
from app.models.enums import PriceTypeEnum, OrderTypeEnum, OrderStatusEnum
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInUpdate, OrderInUpdateStatus
from app.models.schemas.orders import OrderInCreate, OrderInCreateViewResponse
from app.services.engines.base import BaseEngine
from app.services.engines.log_engine import LogEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.user_engine import UserEngine, Event
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from app.services.engines.event_constants import (
    ORDER_CREATE_EVENT,
    ORDER_UPDATE_EVENT,
    ORDER_UPDATE_STATUS_EVENT,
)


class MainEngine(BaseEngine):
    def __init__(self, db: AsyncIOMotorClient, event_engine: Type[EventEngine] = None) -> None:
        super().__init__()
        self.event_engine = event_engine() if event_engine else EventEngine()
        self.db = db
        self.log_engine = LogEngine(self.event_engine)
        self.order_repo = OrderRepository(db[settings.db.name])
        self.user_engine = UserEngine(self.event_engine, self.db)
        self.market_engine = MARKET_NAME_MAPPING[settings.service.market](
            self.event_engine, self.user_engine
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
        self.event_engine.register(ORDER_UPDATE_STATUS_EVENT, self.process_order_status_update)

    def process_order_create(self, payload: OrderInDB) -> None:
        self.order_repo.process_create_order(payload)

    def process_order_update(self, payload: OrderInUpdate) -> None:
        self.order_repo.process_update_order(payload)

    def process_order_status_update(self, payload: OrderInUpdateStatus) -> None:
        self.order_repo.process_update_order_status(payload)

    async def on_order_arrived(self, order: OrderInCreate, user: UserInDB) -> OrderInCreateViewResponse:
        """新订单到达."""
        turnover = await self.user_engine.pre_trade_validation(order, user)
        # 根据订单的股票价格确定价格类型
        order.price_type = PriceTypeEnum.MARKET if str(order.price) == "0" else PriceTypeEnum.LIMIT
        order_in_db = OrderInDB(**dict(order), user=user.id, order_date=datetime.utcnow(),
                                order_id=PyObjectId(), turnover=turnover)
        order_create_event = Event(ORDER_CREATE_EVENT, order_in_db)
        self.event_engine.put(order_create_event)
        self.put_order(order_in_db)
        return OrderInCreateViewResponse(**dict(order_in_db))

    def put_order(self, order: OrderInDB) -> None:
        # 取消订单
        if order.order_type == OrderTypeEnum.CANCEL.value:
            # TODO: 从队列中移除该项
            payload = OrderInUpdateStatus(id=order.id, status=OrderStatusEnum.CANCELED)
            event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
            self.event_engine.put(event)
        # 清算订单
        elif order.order_type == OrderTypeEnum.LIQUIDATION.value:
            pass
        else:
            self.market_engine.exchange_validation(order)
            payload = OrderInUpdateStatus(id=order.id, status=OrderStatusEnum.WAITING)
            event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
            self.event_engine.put(event)
            self.write_log(f"收到新订单: [{order.order_id}].")
            self.market_engine.entrust_queue.put(order)
