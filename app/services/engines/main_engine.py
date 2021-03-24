from typing import Type

from motor.motor_asyncio import AsyncIOMotorDatabase

from app import settings
from app.db.repositories.order import OrderRepository
from app.db.repositories.statement import StatementRepository
from app.models.base import get_utc_now
from app.models.domain.orders import OrderInDB
from app.models.domain.statement import StatementInDB
from app.models.enums import OrderStatusEnum, OrderTypeEnum, PriceTypeEnum
from app.models.schemas.orders import (
    OrderInCreate,
    OrderInCreateViewResponse,
    OrderInUpdate,
    OrderInUpdateFrozen,
    OrderInUpdateStatus,
)
from app.models.schemas.statement import StatementInCreateEvent
from app.models.schemas.users import UserInCache
from app.models.types import PyDecimal, PyObjectId
from app.services.engines.base import BaseEngine
from app.services.engines.event_constants import (
    MARKET_CLOSE_EVENT,
    ORDER_CREATE_EVENT,
    ORDER_UPDATE_EVENT,
    ORDER_UPDATE_FROZEN_EVENT,
    ORDER_UPDATE_STATUS_EVENT,
    STATEMENT_CREATE_EVENT,
)
from app.services.engines.event_engine import EventEngine
from app.services.engines.log_engine import LogEngine
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from app.services.engines.user_engine import Event, UserEngine


class MainEngine(BaseEngine):
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        event_engine: Type[EventEngine] = None,
    ) -> None:
        super().__init__()
        self.event_engine = event_engine() if event_engine else EventEngine()
        self.db = db
        self.log_engine = LogEngine(self.event_engine)
        self.order_repo = OrderRepository(db)
        self.statement_repo = StatementRepository(db)
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
        await self.event_engine.register(
            ORDER_UPDATE_STATUS_EVENT, self.process_order_status_update
        )
        await self.event_engine.register(
            MARKET_CLOSE_EVENT, self.process_refuse_entrust_orders
        )
        await self.event_engine.register(
            ORDER_UPDATE_FROZEN_EVENT, self.process_order_frozen_update
        )
        await self.event_engine.register(
            STATEMENT_CREATE_EVENT, self.process_statement_create
        )

    async def process_order_create(self, payload: OrderInDB) -> None:
        await self.order_repo.process_create_order(payload)

    async def process_order_update(self, payload: OrderInUpdate) -> None:
        await self.order_repo.process_update_order(payload)

    async def process_order_status_update(self, payload: OrderInUpdateStatus) -> None:
        await self.order_repo.process_update_order_status(payload)

    async def process_order_frozen_update(self, payload: OrderInUpdateFrozen) -> None:
        await self.order_repo.process_update_order_frozen(payload)

    async def process_statement_create(self, payload: StatementInCreateEvent) -> None:
        amount = payload.costs.total.to_decimal() + payload.securities_diff.to_decimal()
        statement_in_db = StatementInDB(
            exchange=payload.order.exchange,
            symbol=payload.order.symbol,
            entrust_id=payload.order.entrust_id,
            user=payload.order.user,
            trade_category=payload.order.order_type.value,
            volume=payload.order.traded_volume,
            sold_price=payload.order.sold_price,
            costs=payload.costs,
            amount=-amount if payload.order.order_type == OrderTypeEnum.BUY else amount,
            deal_time=payload.order.deal_time,
        )
        await self.statement_repo.create_statement(statement_in_db)

    async def process_refuse_entrust_orders(self, *args) -> None:
        """将待处理订单列表中的订单状态设置为拒单."""
        orders = await self.order_repo.get_orders(
            status=[OrderStatusEnum.NOT_DONE],
            start_date=get_utc_now().date(),
            end_date=get_utc_now().date(),
        )
        for order in orders:
            await self.refuse_order(order)

    async def refuse_order(self, order: OrderInDB) -> None:
        """设置订单状态为拒单."""
        order.status = OrderStatusEnum.REJECTED
        order_in_update_payload = OrderInUpdate(**dict(order))
        await self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))

    async def on_order_arrived(
        self, order: OrderInCreate, user: UserInCache
    ) -> OrderInCreateViewResponse:
        """新订单到达."""
        frozen = await self.user_engine.pre_trade_validation(order, user)
        # 根据订单的股票价格确定价格类型
        order.price_type = (
            PriceTypeEnum.MARKET if str(order.price) == "0" else PriceTypeEnum.LIMIT
        )
        order_in_db = OrderInDB(
            **dict(order),
            user=user.id,
            order_date=get_utc_now(),
            entrust_id=PyObjectId()
        )
        if order.order_type == OrderTypeEnum.BUY:
            order_in_db.frozen_amount = PyDecimal(frozen)
        else:
            order_in_db.frozen_stock_volume = frozen
        order_create_event = Event(ORDER_CREATE_EVENT, order_in_db)
        await self.event_engine.put(order_create_event)
        order_in_db.id = None
        await self.market_engine.put(order_in_db)
        return OrderInCreateViewResponse(**dict(order_in_db))

    async def load_entrust_orders(self):
        """加载当日未完成的委托订单."""
        entrust_orders = await self.order_repo.get_orders(
            status=[
                OrderStatusEnum.NOT_DONE,
                OrderStatusEnum.SUBMITTING,
                OrderStatusEnum.PART_FINISHED,
            ],
            start_date=get_utc_now().date(),
            end_date=get_utc_now().date(),
        )
        for entrust_order in entrust_orders:
            await self.market_engine.put(entrust_order)
