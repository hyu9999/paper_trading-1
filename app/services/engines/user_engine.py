from decimal import Decimal
from typing import Union, Tuple

from hq2redis.exceptions import EntityNotFound
from motor.motor_asyncio import AsyncIOMotorDatabase
from hq2redis import HQ2Redis

from app.db.repositories.statement import StatementRepository
from app.db.repositories.user import UserRepository
from app.db.repositories.position import PositionRepository
from app.db.repositories.user_assets_record import UserAssetsRecordRepository
from app.exceptions.service import InsufficientFunds, NoPositionsAvailable, NotEnoughAvailablePositions
from app.models.base import get_utc_now
from app.models.types import PyDecimal
from app.models.domain.users import UserInDB
from app.models.domain.statement import Costs
from app.models.domain.orders import OrderInDB
from app.models.enums import OrderTypeEnum, TradeTypeEnum
from app.models.schemas.users import UserInUpdateCash, UserInUpdate
from app.models.schemas.orders import OrderInCreate, OrderInUpdateFrozen
from app.models.schemas.user_assets_records import UserAssetsRecordInCreate, UserAssetsRecordInUpdate
from app.models.schemas.position import PositionInCreate, PositionInUpdateAvailable, PositionInUpdate
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import (
    USER_UPDATE_EVENT,
    USER_UPDATE_CASH_EVENT,
    POSITION_CREATE_EVENT,
    POSITION_UPDATE_EVENT,
    POSITION_UPDATE_AVAILABLE_EVENT,
    USER_ASSETS_RECORD_CREATE_EVENT,
    USER_ASSETS_RECORD_UPDATE_EVENT,
    MARKET_CLOSE_EVENT,
    UNFREEZE_EVENT,
    ORDER_UPDATE_FROZEN_EVENT,
)


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
    def __init__(self, event_engine: EventEngine, db: AsyncIOMotorDatabase, quotes_api: HQ2Redis) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.quotes_api = quotes_api
        self.user_repo = UserRepository(db)
        self.position_repo = PositionRepository(db)
        self.user_assets_record_repo = UserAssetsRecordRepository(db)
        self.statement_repo = StatementRepository(db)

    async def startup(self) -> None:
        await self.register_event()

    async def shutdown(self) -> None:
        pass

    async def register_event(self) -> None:
        await self.event_engine.register(USER_UPDATE_CASH_EVENT, self.process_user_update_cash_event)
        await self.event_engine.register(POSITION_CREATE_EVENT, self.process_position_create_event)
        await self.event_engine.register(USER_UPDATE_EVENT, self.process_user_update_event)
        await self.event_engine.register(POSITION_UPDATE_AVAILABLE_EVENT, self.process_position_update_available)
        await self.event_engine.register(POSITION_UPDATE_EVENT, self.process_position_update)
        await self.event_engine.register(USER_ASSETS_RECORD_CREATE_EVENT, self.process_user_assets_record_create)
        await self.event_engine.register(USER_ASSETS_RECORD_UPDATE_EVENT, self.process_user_assets_record_update)
        await self.event_engine.register(MARKET_CLOSE_EVENT, self.process_market_close)
        await self.event_engine.register(UNFREEZE_EVENT, self.process_unfreeze)

    async def process_user_update_cash_event(self, payload: UserInUpdateCash) -> None:
        await self.user_repo.process_update_user_cash(payload)

    async def process_position_create_event(self, payload: PositionInCreate) -> None:
        await self.position_repo.process_create_position(payload)

    async def process_user_update_event(self, payload: UserInUpdate) -> None:
        await self.user_repo.process_update_user(payload)

    async def process_position_update_available(self, payload: PositionInUpdateAvailable) -> None:
        await self.position_repo.process_update_position_available_by_id(payload)

    async def process_position_update(self, payload: PositionInUpdate) -> None:
        await self.position_repo.process_update_position(payload)

    async def process_user_assets_record_create(self, payload: UserAssetsRecordInCreate) -> None:
        await self.user_assets_record_repo.process_create_user_assets_record(payload)

    async def process_user_assets_record_update(self, payload: UserAssetsRecordInUpdate) -> None:
        await self.user_assets_record_repo.process_update_user_assets_record(payload)

    async def process_market_close(self, *args) -> None:
        users = await self.user_repo.get_users_list()
        for user in users:
            await self.liquidate_user_position(user, is_update_volume=True)
            await self.liquidate_user_profit(user)
            await self.update_user_assets_record(user)

    async def process_unfreeze(self, payload: OrderInDB) -> None:
        """解除预先冻结的资金或持仓股票数量."""
        if payload.frozen_amount:
            user = await self.user_repo.get_user_by_id(payload.user)
            user_in_update = UserInUpdate(**user.dict())
            user_in_update.cash = PyDecimal(payload.frozen_amount.to_decimal() + user.cash.to_decimal())
            await self.user_repo.process_update_user(user_in_update)
        if payload.frozen_stock_volume:
            position = await self.position_repo.get_position(user_id=payload.user, symbol=payload.symbol,
                                                             exchange=payload.exchange)
            position_in_update = PositionInUpdate(**position.dict())
            position_in_update.available_volume += payload.frozen_stock_volume
            await self.position_repo.process_update_position(position_in_update)
        order_in_update_frozen = OrderInUpdateFrozen(entrust_id=payload.entrust_id)
        await self.event_engine.put(Event(ORDER_UPDATE_FROZEN_EVENT, order_in_update_frozen))

    async def pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> Union[PyDecimal, int]:
        """订单创建前用户相关验证."""
        if order.order_type == OrderTypeEnum.BUY:
            return await self.__capital_validation(order, user)
        else:
            return await self.__position_validation(order, user)

    async def __capital_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> PyDecimal:
        """用户资金校验."""
        cash_needs = Decimal(order.volume) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            frozen_cash = PyDecimal(user.cash.to_decimal() - cash_needs)
            payload = UserInUpdateCash(id=user.id, cash=frozen_cash)
            event = Event(USER_UPDATE_CASH_EVENT, payload)
            await self.event_engine.put(event)
            return cash_needs
        else:
            raise InsufficientFunds

    async def __position_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> int:
        """用户持仓检查."""
        position = await self.position_repo.get_position(user.id, order.symbol, order.exchange)
        if position:
            if position.available_volume >= order.volume:
                frozen_stock_volume = position.available_volume - order.volume
                event = Event(
                    POSITION_UPDATE_AVAILABLE_EVENT,
                    PositionInUpdateAvailable(
                        id=position.id,
                        available_volume=frozen_stock_volume
                    )
                )
                await self.event_engine.put(event)
                return order.volume
            raise NotEnoughAvailablePositions
        else:
            raise NoPositionsAvailable

    async def create_position(self, order: OrderInDB) -> Tuple[Decimal, Costs]:
        """新建持仓."""
        position = await self.position_repo.get_position(order.user, order.symbol, order.exchange)
        user = await self.user_repo.get_user_by_id(order.user)
        # 根据交易类别判断持仓股票可用数量
        order_available_volume = order.traded_volume if order.trade_type == TradeTypeEnum.T0 else 0
        # 订单证券市值
        securities = Decimal(order.traded_volume) * order.sold_price.to_decimal()
        # 交易佣金
        commission = securities * user.commission.to_decimal()
        # 增持股票
        if position:
            volume = position.volume + order.traded_volume
            current_price = order.sold_price
            # 持仓成本 = ((原持仓数 * 原持仓成本) + (订单交易数 * 订单交易价格)) / 持仓总量
            cost = ((Decimal(position.volume) * position.cost.to_decimal()) +
                    (Decimal(order.traded_volume) * order.sold_price.to_decimal())) / volume
            available_volume = position.available_volume + order_available_volume
            # 持仓利润 = (现交易价格 - 原持仓记录的价格) * 原持有数量 + 原利润 - 交易费用
            profit = (order.sold_price.to_decimal() - position.current_price.to_decimal()
                      ) * Decimal(position.volume) + position.profit.to_decimal() - commission
            position_in_update = PositionInUpdate(
                id=position.id,
                volume=volume,
                current_price=current_price,
                cost=PyDecimal(cost),
                available_volume=available_volume,
                profit=PyDecimal(profit)
            )
            event = Event(POSITION_UPDATE_EVENT, position_in_update)
            await self.event_engine.put(event)
            # 证券资产变化值 = 现持仓市值 - 原持仓市值
            securities_diff = volume * current_price.to_decimal() - \
                Decimal(position.volume) * position.current_price.to_decimal()
        # 建仓
        else:
            # 证券资产变化值 = 订单证券市值
            securities_diff = securities
            # 可用股票数量
            position_in_create = PositionInCreate(
                user=order.user,
                symbol=order.symbol,
                exchange=order.exchange,
                volume=order.traded_volume,
                available_volume=order_available_volume,
                cost=order.sold_price,
                current_price=order.sold_price,
                profit=-commission,
                first_buy_date=get_utc_now()
            )
            await self.event_engine.put(Event(POSITION_CREATE_EVENT, position_in_create))
        costs = Costs(commission=commission, total=commission, tax="0")
        await self.update_user(order, securities_diff, costs)
        return securities_diff, costs

    async def reduce_position(self, order: OrderInDB) -> Tuple[Decimal, Costs]:
        """减仓."""
        position = await self.position_repo.get_position(order.user, order.symbol, order.exchange)
        user = await self.user_repo.get_user_by_id(order.user)
        commission = Decimal(order.volume) * order.price.to_decimal() * user.commission.to_decimal()
        volume = position.volume - order.traded_volume
        current_price = order.sold_price
        tax = Decimal(order.traded_volume) * order.sold_price.to_decimal() * user.tax_rate.to_decimal()
        # 持仓利润 = (现交易价格 - 原持仓记录的价格) * 原持仓数量 + 原持仓利润 - 交易佣金 - 印花税
        profit = (order.sold_price.to_decimal() - position.current_price.to_decimal()
                  ) * Decimal(position.volume) + position.profit.to_decimal() - commission - tax
        # 可用持仓 = 原持仓数 + 冻结的股票数量 - 交易成功的股票数量
        available_volume = position.available_volume + order.frozen_stock_volume - order.traded_volume
        # 持仓成本 = ((原持仓量 * 原持仓价) - (订单交易量 * 订单交易价 * 交易费率)) / 持仓数量
        old_spent = Decimal(position.volume) * position.cost.to_decimal()
        new_spent = Decimal(order.traded_volume) * order.sold_price.to_decimal() * \
            (Decimal(1) - user.commission.to_decimal() - user.tax_rate.to_decimal())
        cost = (old_spent - new_spent) / volume if volume else "0"
        position_in_update = PositionInUpdate(
            id=position.id,
            volume=volume,
            current_price=current_price,
            cost=PyDecimal(cost),
            available_volume=available_volume,
            profit=PyDecimal(profit)
        )
        # 清仓
        if volume == 0:
            position_in_update.last_sell_date = get_utc_now()
        event = Event(POSITION_UPDATE_EVENT, position_in_update)
        await self.event_engine.put(event)
        costs = Costs(commission=commission, tax=tax, total=commission+tax)
        # 证券资产变化值 = 订单证券市值
        securities_diff = Decimal(order.traded_volume) * order.sold_price.to_decimal()
        await self.update_user(order, securities_diff, costs)
        return securities_diff, costs

    async def update_user(self, order: OrderInDB, securities_diff: Decimal, costs: Costs) -> None:
        """订单成交后更新用户信息."""
        user = await self.user_repo.get_user_by_id(order.user)
        if order.order_type == OrderTypeEnum.BUY:
            # 可用现金 = 原现金 + 预先冻结的现金 - 证券市值 - 减实际花费的现金
            cash = user.cash.to_decimal() + order.frozen_amount.to_decimal() - securities_diff - \
                   costs.total.to_decimal()
            # 证券资产 = 原证券资产 + 证券资产的变化值
            securities = user.securities.to_decimal() + securities_diff
        else:
            # 可用现金 = 原现金 + 证券资产变化值 - 手续费
            cash = user.cash.to_decimal() + securities_diff - costs.total.to_decimal()
            # 证券资产 = 原证券资产 - 证券资产的变化值
            # 若证券资产的变化值, 则代表账户证券资产未及时更新 先按0处理 同步资产任务会矫正
            if user.securities.to_decimal() > securities_diff:
                securities = user.securities.to_decimal() - securities_diff
            else:
                securities = Decimal("0")
        # 总资产 = 现金 + 证券资产
        assets = cash + securities
        user_in_update = UserInUpdate(id=user.id, cash=PyDecimal(cash), securities=PyDecimal(securities),
                                      assets=PyDecimal(assets))
        await self.event_engine.put(Event(USER_UPDATE_EVENT, user_in_update))

    async def update_user_assets_record(self, user: UserInDB) -> None:
        """更新用户资产时点数据."""
        record = await self.user_assets_record_repo.get_user_assets_record_today(user_id=user.id)
        if record:
            record_in_update = UserAssetsRecordInUpdate(
                id=record.id, assets=user.assets, cash=user.cash, securities=user.securities
            )
            event = Event(USER_ASSETS_RECORD_UPDATE_EVENT, record_in_update)
            await self.event_engine.put(event)
        else:
            record_in_create = UserAssetsRecordInCreate(
                user=user.id, assets=user.assets, cash=user.cash, securities=user.securities, date=get_utc_now()
            )
            event = Event(USER_ASSETS_RECORD_CREATE_EVENT, record_in_create)
            await self.event_engine.put(event)

    async def liquidate_user_position(self, user: UserInDB, is_update_volume: int = False) -> None:
        """清算用户持仓数据."""
        user_position = await self.position_repo.get_positions_by_user_id(user_id=user.id)
        for position in user_position:
            try:
                quotes = await self.quotes_api.get_stock_ticks(position.stock_code)
            except EntityNotFound:
                await self.write_log(f"未找到股票{position.stock_code}的行情信息.")
                continue
            current_price = quotes.ask1_p
            position_in_update = PositionInUpdate(**position.dict())
            position_in_update.current_price = PyDecimal(current_price)
            # 更新可用股票数量
            if is_update_volume:
                position_in_update.available_volume = position.volume
            statement_list = await self.statement_repo.get_statement_list_by_symbol(user.id, position.symbol)
            # 持仓利润 = 现价 * 持仓数量 - 该持仓交易总费用
            profit = current_price * Decimal(position.volume) \
                - sum(statement.costs.total.to_decimal() for statement in statement_list)
            position_in_update.profit = PyDecimal(profit)
            await self.position_repo.process_update_position(position_in_update)

    async def liquidate_user_profit(self, user: UserInDB) -> UserInUpdate:
        """清算用户个人数据."""
        user_position = await self.position_repo.get_positions_by_user_id(user_id=user.id)
        securities = sum([position.current_price.to_decimal() * Decimal(position.volume)
                          for position in user_position])
        assets = user.cash.to_decimal() + securities
        user_in_update = UserInUpdate(**user.dict())
        if securities != Decimal(0):
            user_in_update.securities = PyDecimal(securities)
        user_in_update.assets = PyDecimal(assets)
        await self.user_repo.process_update_user(user_in_update, exclude=["cash"])
        return user_in_update
