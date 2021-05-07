import asyncio
import itertools
from decimal import Decimal
from typing import Tuple, Union

from hq2redis.exceptions import SecurityNotFoundError
from hq2redis.reader import get_security_price
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from pymongo import DeleteOne, UpdateOne

from app import state
from app.db.cache.position import PositionCache
from app.db.cache.user import UserCache
from app.db.repositories.position import PositionRepository
from app.db.repositories.statement import StatementRepository
from app.db.repositories.user import UserRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.service import (
    InsufficientFunds,
    NoPositionsAvailable,
    NotEnoughAvailablePositions,
)
from app.models.base import get_utc_now
from app.models.domain.orders import OrderInDB
from app.models.domain.statement import Costs
from app.models.enums import OrderTypeEnum, TradeTypeEnum
from app.models.schemas.orders import OrderInCreate
from app.models.schemas.position import PositionInCache
from app.models.schemas.users import UserInCache
from app.models.types import PyDecimal, PyObjectId
from app.services.engines.base import BaseEngine
from app.services.engines.event_constants import (
    MARKET_CLOSE_EVENT,
    POSITION_CREATE_EVENT,
    POSITION_UPDATE_EVENT,
    UNFREEZE_EVENT,
    USER_UPDATE_ASSETS_EVENT,
    USER_UPDATE_AVAILABLE_CASH_EVENT,
    USER_UPDATE_EVENT,
)
from app.services.engines.event_engine import Event, EventEngine


class UserEngine(BaseEngine):
    """用户引擎.

    Raises
    ------
    InsufficientFunds
        资金不足时触发
    NoPositionsAvailable
        用户未持有卖单指定的股票时触发
    NotEnoughAvailablePositions
        用户持仓股票可用数量不够买单指定的数量时触发
    """

    def __init__(
        self,
        event_engine: EventEngine,
        db: AsyncIOMotorDatabase,
    ) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.user_repo = UserRepository(db)
        self.position_repo = PositionRepository(db)
        self.user_cache = UserCache(state.user_redis_pool)
        self.position_cache = PositionCache(state.position_redis_pool)
        self.statement_repo = StatementRepository(db)

    async def startup(self) -> None:
        await self.load_db_data_to_redis()
        await self.register_event()

    async def shutdown(self) -> None:
        pass

    async def load_db_data_to_redis(self) -> None:
        """加载MongoDB的数据到Redis."""
        if await self.user_cache.is_reload:
            user_list = await self.user_repo.get_user_list_to_cache()
            await self.user_cache.set_user_many(user_list)
            position_list = await asyncio.gather(
                *(
                    self.position_repo.get_positions_by_user_id_to_cache(user.id)
                    for user in user_list
                )
            )
            position_in_cache_list = list(itertools.chain.from_iterable(position_list))
            if position_in_cache_list:
                await self.position_cache.set_position_many(position_in_cache_list)

    async def load_redis_data_to_db(self) -> None:
        """加载Redis的数据到MongoDB."""
        user_list = await self.user_cache.get_all_user()
        update_user_list = []
        update_position_list = []
        delete_position_list = []
        for user in user_list:
            update_user_list.append(
                UpdateOne({"_id": user.id}, {"$set": user.dict(exclude={"id"})})
            )
            position_list = await self.position_repo.get_positions_by_user_id(user.id)
            for position in position_list:
                try:
                    position_in_cache = await self.position_cache.get_position(
                        user.id, position.symbol, position.exchange
                    )
                except EntityDoesNotExist:
                    delete_position_list.append(DeleteOne({"_id": position.id}))
                else:
                    update_position_list.append(
                        UpdateOne(
                            {
                                "user": position.user,
                                "symbol": position.symbol,
                                "exchange": position.exchange,
                            },
                            {"$set": position_in_cache.dict()},
                        )
                    )
        if update_user_list:
            await self.user_repo.bulk_update(update_user_list)
        if update_position_list:
            await self.position_repo.bulk_update(update_position_list)
        if delete_position_list:
            await self.position_repo.bulk_delete(delete_position_list)

    async def register_event(self) -> None:
        await self.event_engine.register(
            POSITION_CREATE_EVENT, self.process_position_create
        )
        await self.event_engine.register(USER_UPDATE_EVENT, self.process_user_update)
        await self.event_engine.register(
            POSITION_UPDATE_EVENT, self.process_position_update
        )
        await self.event_engine.register(MARKET_CLOSE_EVENT, self.process_market_close)
        await self.event_engine.register(UNFREEZE_EVENT, self.process_unfreeze)
        await self.event_engine.register(
            USER_UPDATE_AVAILABLE_CASH_EVENT, self.process_user_update_available_cash
        )
        await self.event_engine.register(
            USER_UPDATE_ASSETS_EVENT, self.process_user_update_assets
        )

    async def process_user_update(self, payload: UserInCache) -> None:
        await self.user_cache.update_user(payload)

    async def process_user_update_available_cash(self, payload: UserInCache) -> None:
        await self.user_cache.update_user(payload, include={"available_cash"})

    async def process_user_update_assets(self, payload: UserInCache) -> None:
        await self.user_cache.update_user(
            payload, include={"cash", "securities", "assets", "available_cash"}
        )

    async def process_position_create(self, payload: PositionInCache) -> None:
        await self.position_cache.set_position(payload)

    async def process_position_update(self, payload: PositionInCache) -> None:
        await self.position_cache.update_position(payload)

    async def process_market_close(self, *args) -> None:
        await self.write_log("收盘清算开始...")
        users = await self.user_cache.get_all_user()
        for user in users:
            await self.write_log(f"正在清算用户`{user.id}`的数据.")
            await self.liquidate_user_position(user.id, is_update_volume=True)
            await self.liquidate_user_profit(user.id, is_refresh_frozen_amount=True)
        await self.write_log("收盘清算结束.")
        await self.load_redis_data_to_db()

    async def process_unfreeze(self, payload: OrderInDB) -> None:
        """解除预先冻结的资金或持仓股票数量."""
        if payload.frozen_amount:
            user = await self.user_cache.get_user_by_id(payload.user)
            user.available_cash = PyDecimal(
                payload.frozen_amount.to_decimal() + user.available_cash.to_decimal()
            )
            await self.user_cache.update_user(user, include={"available_cash"})
        if payload.frozen_stock_volume:
            position = await self.position_cache.get_position(
                user_id=payload.user, symbol=payload.symbol, exchange=payload.exchange
            )
            position.available_volume += payload.frozen_stock_volume
            await self.position_cache.update_position(
                position, include={"available_volume"}
            )

    async def pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInCache,
    ) -> Union[PyDecimal, int]:
        """订单创建前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await self.__capital_validation(order, user)
        else:
            return await self.__position_validation(order, user)

    async def __capital_validation(
        self,
        order: OrderInCreate,
        user: UserInCache,
    ) -> PyDecimal:
        """用户资金校验."""
        cash_needs = (
            Decimal(order.volume)
            * order.price.to_decimal()
            * (1 + user.commission.to_decimal())
        )
        # 若用户现金可以满足订单需求
        if user.available_cash.to_decimal() >= cash_needs:
            user.available_cash = PyDecimal(
                user.available_cash.to_decimal() - cash_needs
            )
            await self.user_cache.update_user(user, include={"available_cash"})
            return cash_needs
        else:
            raise InsufficientFunds

    async def __position_validation(
        self,
        order: OrderInCreate,
        user: UserInCache,
    ) -> int:
        """用户持仓检查."""
        try:
            position = await self.position_cache.get_position(
                user.id, order.symbol, order.exchange
            )
        except EntityDoesNotExist:
            raise NoPositionsAvailable
        else:
            if position.available_volume >= order.volume:
                position.available_volume -= order.volume
                await self.position_cache.update_position(
                    position, include={"available_volume"}
                )
                return order.volume
            raise NotEnoughAvailablePositions

    async def create_position(self, order: OrderInDB) -> Tuple[Decimal, Costs]:
        """新建持仓."""
        user = await self.user_cache.get_user_by_id(order.user)
        # 根据交易类别判断持仓股票可用数量
        order_available_volume = (
            order.traded_volume if order.trade_type == TradeTypeEnum.T0 else 0
        )
        # 行情
        quotes = await get_security_price(order.stock_code)
        # 订单证券市值
        securities_order = Decimal(order.traded_volume) * order.sold_price.to_decimal()
        # 证券资产变化值
        securities_diff = Decimal(order.traded_volume) * quotes.current
        # 交易佣金
        commission = securities_order * user.commission.to_decimal()
        # 订单交易金额
        amount = commission + securities_order
        order_profit = (quotes.current - order.sold_price.to_decimal()) * Decimal(
            order.traded_volume
        ) - commission
        try:
            position = await self.position_cache.get_position(
                order.user, order.symbol, order.exchange
            )
        except EntityDoesNotExist:
            # 持仓成本 = 总花费 / 交易数量
            cost = amount / order.traded_volume
            # 建仓
            new_position = PositionInCache(
                user=order.user,
                symbol=order.symbol,
                exchange=order.exchange,
                volume=order.traded_volume,
                available_volume=order_available_volume,
                cost=PyDecimal(cost),
                current_price=PyDecimal(quotes.current),
                profit=order_profit,
                first_buy_date=get_utc_now(),
            )
            await self.event_engine.put(Event(POSITION_CREATE_EVENT, new_position))
        else:
            volume = position.volume + order.traded_volume
            # 持仓成本 = (原持仓数 * 原持仓成本) + 总花费 / 持仓总量
            cost = (
                Decimal(position.volume) * position.cost.to_decimal() + amount
            ) / volume
            available_volume = position.available_volume + order_available_volume
            # 持仓利润 = (现价 - 成本价) * 持仓数量
            profit = (quotes.current - cost) * Decimal(volume)
            position.volume = volume
            position.available_volume = available_volume
            position.current_price = quotes.current
            position.cost = PyDecimal(cost)
            position.profit = PyDecimal(profit)
            event = Event(POSITION_UPDATE_EVENT, position)
            await self.event_engine.put(event)
        costs = Costs(commission=commission, total=commission, tax="0")
        await self.update_user(order, amount, securities_diff)
        return securities_order, costs

    async def reduce_position(self, order: OrderInDB) -> Tuple[Decimal, Costs]:
        """减仓."""
        position = await self.position_cache.get_position(
            order.user, order.symbol, order.exchange
        )
        user = await self.user_cache.get_user_by_id(order.user)
        commission = (
            Decimal(order.traded_volume)
            * order.sold_price.to_decimal()
            * user.commission.to_decimal()
        )
        tax = (
            Decimal(order.traded_volume)
            * order.sold_price.to_decimal()
            * user.tax_rate.to_decimal()
        )
        volume = position.volume - order.traded_volume
        # 行情
        quotes = await get_security_price(order.stock_code)
        # 原持仓成本
        old_spent = Decimal(position.volume) * position.cost.to_decimal()
        # 清仓
        if volume == 0:
            # 持仓成本 = (原总成本 + 佣金 + 税) / 数量
            cost = (old_spent + commission + tax) / order.traded_volume
            # 持仓利润 = (现价 - 成本) * 持仓量
            profit = (quotes.current - cost) * order.traded_volume
            position.volume = 0
            position.available_volume = 0
            position.current_price = PyDecimal(quotes.current)
            position.cost = PyDecimal(cost)
            position.profit = PyDecimal(profit)
            event = Event(POSITION_UPDATE_EVENT, position)
            await self.event_engine.put(event)
        # 减仓
        else:
            # 可用持仓 = 原持仓数 + 冻结的股票数量 - 交易成功的股票数量
            available_volume = (
                position.available_volume
                + order.frozen_stock_volume
                - order.traded_volume
            )
            # 持仓成本 = ((原总成本 + 佣金 + 税) - (订单交易价 * 订单成交数量)) / 剩余数量
            cost = (
                (old_spent + commission + tax)
                - (order.sold_price.to_decimal() * Decimal(order.traded_volume))
            ) / volume
            # 持仓利润 = (现价 - 持仓例如) * 持仓数量
            profit = (quotes.current - cost) * Decimal(volume)
            position.volume = volume
            position.available_volume = available_volume
            position.current_price = PyDecimal(quotes.current)
            position.cost = PyDecimal(cost)
            position.profit = PyDecimal(profit)
            event = Event(POSITION_UPDATE_EVENT, position)
            await self.event_engine.put(event)
        costs = Costs(commission=commission, tax=tax, total=commission + tax)
        # 证券资产变化值 = 订单证券市值
        securities_diff = Decimal(order.traded_volume) * order.sold_price.to_decimal()
        amount = securities_diff - commission - tax
        await self.update_user(order, amount, securities_diff)
        return securities_diff, costs

    async def update_user(
        self, order: OrderInDB, amount: Decimal, securities_diff: Decimal
    ) -> None:
        """订单成交后更新用户信息."""
        user = await self.user_cache.get_user_by_id(order.user)
        if order.order_type == OrderTypeEnum.BUY:
            # 现金 = 原现金 - 订单交易金额
            cash = user.cash.to_decimal() - amount
            available_cash = (
                user.available_cash.to_decimal()
                + order.frozen_amount.to_decimal()
                - amount
            )
            # 证券资产 = 原证券资产 + 证券资产的变化值
            securities = user.securities.to_decimal() + securities_diff
        else:
            # 可用现金 = 原现金 + 收益
            cash = user.cash.to_decimal() + amount
            available_cash = user.available_cash.to_decimal() + amount
            # 证券资产 = 原证券资产 - 证券资产的变化值
            securities = user.securities.to_decimal() - securities_diff
        # 总资产 = 现金 + 证券资产
        assets = cash + securities
        user.cash = PyDecimal(cash)
        user.securities = PyDecimal(securities or "0")
        user.assets = PyDecimal(assets)
        user.available_cash = PyDecimal(available_cash)
        await self.event_engine.put(Event(USER_UPDATE_ASSETS_EVENT, user))

    async def liquidate_user_position(
        self, user_id: PyObjectId, is_update_volume: int = False
    ) -> None:
        """清算用户持仓数据."""
        position_list = await self.position_cache.get_position_by_user_id(
            user_id=user_id
        )
        new_position_list = []
        for position in position_list:
            if is_update_volume and position.volume == 0:
                await self.position_cache.delete_position(position)
                continue
            try:
                security = await get_security_price(position.stock_code)
            except (SecurityNotFoundError, ValidationError):
                await self.write_log(f"未找到股票{position.stock_code}的行情信息.")
                continue
            current_price = security.current
            position.current_price = PyDecimal(current_price)
            # 更新可用股票数量
            if is_update_volume:
                position.available_volume = position.volume
            # 持仓利润 = (现价 - 成本价) * 持仓数量
            profit = (current_price - position.cost.to_decimal()) * Decimal(
                position.volume
            )
            position.profit = PyDecimal(profit)
            new_position_list.append(position)
        include = {"current_price", "profit"}
        if is_update_volume:
            include.add("available_volume")
        await self.position_cache.update_position_many(
            new_position_list, include=include
        )

    async def liquidate_user_profit(
        self, user_id: PyObjectId, is_refresh_frozen_amount: bool = False
    ) -> None:
        """清算用户个人数据."""
        user = await self.user_cache.get_user_by_id(user_id)
        position_list = await self.position_cache.get_position_by_user_id(
            user_id=user_id
        )
        securities = sum(
            [
                position.current_price.to_decimal() * Decimal(position.volume)
                for position in position_list
            ]
        )
        user.assets = PyDecimal(user.cash.to_decimal() + securities)
        if securities != Decimal(0):
            user.securities = PyDecimal(securities)
        include = {"assets", "securities"}
        if is_refresh_frozen_amount:
            user.available_cash = user.cash
            include.add("available_cash")
        await self.user_cache.update_user(user, include=include)
