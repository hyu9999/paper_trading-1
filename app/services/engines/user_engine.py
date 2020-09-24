from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.repositories.user import UserRepository
from app.exceptions.service import InsufficientFunds
from app.models.types import PyDecimal
from app.models.enums import OrderTypeEnum
from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate
from app.models.schemas.event_payload import UserInUpdateCashPayload
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import USER_UPDATE_CASH_EVENT


class UserEngine(BaseEngine):
    """用户引擎.

    Raises
    ------
    InsufficientFunds
        资金不足时触发
    """
    def __init__(self, event_engine: EventEngine, db: AsyncIOMotorClient) -> None:
        self.event_engine = event_engine
        self.user_repo = UserRepository(db[settings.db.name])

    def startup(self) -> None:
        self.register_event()

    def shutdown(self) -> None:
        pass

    def register_event(self) -> None:
        self.event_engine.register(USER_UPDATE_CASH_EVENT, self.process_user_update_cash_event)

    def process_user_update_cash_event(self, payload: UserInUpdateCashPayload) -> None:
        self.user_repo.process_update_user_cash(payload)

    async def pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> None:
        """订单创建前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await self.__capital_validation(order, user)
        else:
            return await self.__position_validation(order)

    async def __capital_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> None:
        """用户资金校验."""
        cash_needs = Decimal(order.quantity) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            freeze_cash = PyDecimal(user.cash.to_decimal() - cash_needs)
            payload = UserInUpdateCashPayload(id=user.id, cash=freeze_cash)
            event = Event(USER_UPDATE_CASH_EVENT, payload)
            self.event_engine.put(event)
        else:
            raise InsufficientFunds

    async def __position_validation(
        self,
        order: OrderInCreate,
    ) -> None:
        """用户持仓检查."""
        pass
