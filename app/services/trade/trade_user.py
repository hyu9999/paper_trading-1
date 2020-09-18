from decimal import Decimal

from fastapi import BackgroundTasks, Depends

from app.models.domain.users import UserInDB
from app.models.enums import OrderTypeEnum
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.schemas.orders import OrderInCreate


class TradeUser:

    @classmethod
    async def pre_trade_validation(
        cls,
        order: OrderInCreate,
        user: UserInDB,
        background_task: BackgroundTasks
    ) -> None:
        """订单生成前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await cls.__capital_validation(order, user, background_task)

    @classmethod
    async def __capital_validation(
        cls,
        order: OrderInCreate,
        user: UserInDB,
        background_task: BackgroundTasks,
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    ) -> None:
        """用户资金校验."""
        cash_needs = Decimal(order.quantity) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            user.cash -= cash_needs
            background_task.add_task(user_repo.update_user_by_id, user.id, user.cash)
