from app.models.schemas.orders import OrderInCreate

from app.services.trade.trade_user import TradeUser
from app.models.domain.users import UserInDB
from fastapi import BackgroundTasks


class TradeOrder:

    @classmethod
    async def on_order_arrived(cls, order: OrderInCreate, user: UserInDB, background_task: BackgroundTasks) -> None:
        """订单到达"""
        await TradeUser.pre_trade_validation(order, user, background_task)
