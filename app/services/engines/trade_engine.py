from typing import Type
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import BackgroundTasks

from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate
from app.models.enums import OrderTypeEnum
from app.models.types import PyDecimal
from app.services.engines.event_engine import Event, EventEngine
from app.services.engines.event_constants import USER_UPDATE_EVENT
from app.services.engines.user_engine import UserEngine


class TradeEngine:
    def __init__(self, db: AsyncIOMotorClient, event_engine: Type[EventEngine] = None) -> None:
        self.event_engine = event_engine() if event_engine else EventEngine()
        self.db = db
        self.register_event()
        self.user_engine = UserEngine(self.event_engine, self.db)

    def register_event(self) -> None:
        pass

    async def on_order_arrived(self, order: OrderInCreate, user: UserInDB, background_task: BackgroundTasks):
        await self.__pre_trade_validation(order, user, background_task)

    async def __pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
        background_task: BackgroundTasks
    ) -> None:
        """订单创建前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await self.__capital_validation(order, user, background_task)
        else:
            return await self.__position_validation(order)

    async def __capital_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
        background_task: BackgroundTasks
    ) -> None:
        """用户资金校验."""
        cash_needs = Decimal(order.quantity) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            user.cash = PyDecimal(user.cash.to_decimal() - cash_needs)
            event = Event(USER_UPDATE_EVENT, user)
            await self.event_engine.process(background_task, event)

    async def __position_validation(
        self,
        order: OrderInCreate,
    ) -> None:
        """用户持仓检查"""
        pos_needs = order.quantity