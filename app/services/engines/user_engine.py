from decimal import Decimal
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.repositories.user import UserRepository
from app.db.repositories.position import PositionRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.service import InsufficientFunds
from app.models.domain.orders import OrderInDB
from app.models.schemas.position import PositionInCreate
from app.models.types import PyDecimal
from app.models.enums import OrderTypeEnum, TradeTypeEnum
from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate
from app.models.schemas.users import UserInUpdateCash, UserInUpdate
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import (
    USER_UPDATE_EVENT,
    USER_UPDATE_CASH_EVENT,
    POSITION_CREATE_EVENT,
)


class UserEngine(BaseEngine):
    """用户引擎.

    Raises
    ------
    InsufficientFunds
        资金不足时触发
    """
    def __init__(self, event_engine: EventEngine, db: AsyncIOMotorClient) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.user_repo = UserRepository(db[settings.db.name])
        self.position_repo = PositionRepository(db[settings.db.name])

    def startup(self) -> None:
        self.register_event()

    def shutdown(self) -> None:
        pass

    def register_event(self) -> None:
        self.event_engine.register(USER_UPDATE_CASH_EVENT, self.process_user_update_cash_event)
        self.event_engine.register(POSITION_CREATE_EVENT, self.process_position_create_event)
        self.event_engine.register(USER_UPDATE_EVENT, self.process_user_update_event)

    def process_user_update_cash_event(self, payload: UserInUpdateCash) -> None:
        self.user_repo.process_update_user_cash(payload)

    def process_position_create_event(self, payload: PositionInCreate) -> None:
        self.position_repo.process_create_position(payload)

    def process_user_update_event(self, payload: UserInUpdate):
        self.user_repo.process_update_user(payload)

    async def pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> PyDecimal:
        """订单创建前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await self.__capital_validation(order, user)
        else:
            return await self.__position_validation(order)

    async def __capital_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> PyDecimal:
        """用户资金校验."""
        cash_needs = Decimal(order.quantity) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            freeze_cash = PyDecimal(user.cash.to_decimal() - cash_needs)
            payload = UserInUpdateCash(id=user.id, cash=freeze_cash)
            event = Event(USER_UPDATE_CASH_EVENT, payload)
            self.event_engine.put(event)
            return freeze_cash
        else:
            raise InsufficientFunds

    async def __position_validation(
        self,
        order: OrderInCreate,
    ) -> PyDecimal:
        """用户持仓检查."""
        pass

    async def create_position(self, order: OrderInDB):
        """新建持仓."""
        position = await self.position_repo.get_position(order.user, order.symbol, order.exchange)
        user = await self.user_repo.get_user_by_id(str(order.user))
        # 增持股票
        if position:
            pass
        # 建仓
        else:
            # 可用股票数量
            available_quantity = order.traded_quantity if order.trade_type == TradeTypeEnum.T0 else 0
            position_in_create = PositionInCreate(
                user=order.user,
                symbol=order.symbol,
                exchange=order.exchange,
                quantity=order.traded_quantity,
                available_quantity=available_quantity,
                cost=order.trade_price,
                current_price=order.trade_price,
                profit=-(Decimal(order.quantity) * order.price.to_decimal() * user.commission.to_decimal()),
                first_buy_date=datetime.utcnow()
            )
            self.event_engine.put(Event(POSITION_CREATE_EVENT, position_in_create))
            await self.update_user(order, position_in_create.quantity * position_in_create.current_price.to_decimal())

    async def delete_position(self, order: OrderInDB):
        """取消持仓"""
        pass

    async def update_user(self, order: OrderInDB, securities_diff: Decimal):
        """订单成交后更新用户信息"""
        user = await self.user_repo.get_user_by_id(str(order.user))
        cost = Decimal(order.quantity) * order.trade_price.to_decimal() * (1 + user.commission.to_decimal())
        # 可用现金 = 原现金 + 预先冻结的现金 + 减实际花费的现金
        cash = user.cash.to_decimal() + order.turnover.to_decimal() - cost
        # 证券资产 = 原证券资产 + 证券资产的变化值
        securities = user.securities.to_decimal() + securities_diff
        # 总资产 = 原资产 - 现金花费 + 证券资产变化值
        assets = user.assets.to_decimal() - cost + securities_diff
        user_in_update = UserInUpdate(id=user.id, cash=PyDecimal(cash), securities=PyDecimal(securities), assets=PyDecimal(assets))
        self.event_engine.put(Event(USER_UPDATE_EVENT, user_in_update))
