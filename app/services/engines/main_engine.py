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

    async def startup(self) -> None:
        await self.event_engine.startup()
        await self.log_engine.startup()
        await self.user_engine.startup()
        await self.market_engine.startup()
        await self.register_event()
        await self.load_entrust_orders()

    async def shutdown(self) -> None:
        await self.market_engine.shutdown()
        await self.user_engine.shutdown()
        await self.log_engine.shutdown()
        await self.event_engine.shutdown()

    async def register_event(self) -> None:
        await self.event_engine.register(ORDER_CREATE_EVENT, self.process_order_create)
        await self.event_engine.register(ORDER_UPDATE_EVENT, self.process_order_update)
        await self.event_engine.register(ORDER_UPDATE_STATUS_EVENT, self.process_order_status_update)

    async def process_order_create(self, payload: OrderInDB) -> None:
        await self.order_repo.process_create_order(payload)

    async def process_order_update(self, payload: OrderInUpdate) -> None:
        await self.order_repo.process_update_order(payload)

    async def process_order_status_update(self, payload: OrderInUpdateStatus) -> None:
        await self.order_repo.process_update_order_status(payload)

    async def on_order_arrived(self, order: OrderInCreate, user: UserInDB) -> OrderInCreateViewResponse:
        """新订单到达."""
        turnover = await self.user_engine.pre_trade_validation(order, user)
        # 根据订单的股票价格确定价格类型
        order.price_type = PriceTypeEnum.MARKET if str(order.price) == "0" else PriceTypeEnum.LIMIT
        order_in_db = OrderInDB(**dict(order), user=user.id, order_date=datetime.utcnow(),
                                order_id=PyObjectId(), turnover=turnover)
        order_create_event = Event(ORDER_CREATE_EVENT, order_in_db)
        await self.event_engine.put(order_create_event)

        order_in_db.id = None
        await self.put_order(order_in_db)
        return OrderInCreateViewResponse(**dict(order_in_db))

    async def put_order(self, order: OrderInDB) -> None:
        # 取消订单
        if order.order_type == OrderTypeEnum.CANCEL.value:
            await self.market_engine.entrust_queue.delete(order.order_id)
            payload = OrderInUpdateStatus(order_id=order.order_id, status=OrderStatusEnum.CANCELED)
            event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
            await self.event_engine.put(event)
        # 清算订单
        elif order.order_type == OrderTypeEnum.LIQUIDATION.value:
            pass
        else:
            await self.market_engine.exchange_validation(order)
            payload = OrderInUpdateStatus(order_id=order.order_id, status=OrderStatusEnum.WAITING)
            event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
            await self.event_engine.put(event)
            await self.write_log(f"收到新订单: [{order.order_id}].")
            await self.market_engine.entrust_queue.put(order)

    async def load_entrust_orders(self):
        """加载当日未完成的委托订单."""
        entrust_orders = await self.order_repo.get_orders(
            status=[OrderStatusEnum.WAITING, OrderStatusEnum.PART_FINISHED],
            start_date=datetime.utcnow().date(),
            end_date=datetime.utcnow().date(),
        )
        for entrust_order in entrust_orders:
            await self.market_engine.entrust_queue.put(entrust_order)
