from decimal import Decimal
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.user import UserRepository
from app.db.repositories.position import PositionRepository
from app.db.repositories.user_assets_record import UserAssetsRecordRepository
from app.exceptions.service import InsufficientFunds, NoPositionsAvailable, NotEnoughAvailablePositions
from app.models.types import PyDecimal
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCreate
from app.models.enums import OrderTypeEnum, TradeTypeEnum
from app.models.schemas.users import UserInUpdateCash, UserInUpdate
from app.models.schemas.user_assets_records import UserAssetsRecordInCreate, UserAssetsRecordInUpdate
from app.models.schemas.position import PositionInCreate, PositionInUpdateAvailable, PositionInUpdate
from app.services.quotes.base import BaseQuotes
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import (
    USER_UPDATE_EVENT,
    USER_UPDATE_CASH_EVENT,
    POSITION_CREATE_EVENT,
    POSITION_UPDATE_EVENT,
    POSITION_UPDATE_AVAILABLE_EVENT,
    USER_ASSETS_RECORD_CREATE_EVENT,
    USER_ASSETS_RECORD_UPDATE_EVENT
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
    def __init__(self, event_engine: EventEngine, db: AsyncIOMotorDatabase, quotes_api: BaseQuotes) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.quotes_api = quotes_api
        self.user_repo = UserRepository(db)
        self.position_repo = PositionRepository(db)
        self.user_assets_record_repo = UserAssetsRecordRepository(db)

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

    async def process_user_update_cash_event(self, payload: UserInUpdateCash) -> None:
        await self.user_repo.process_update_user_cash(payload)

    async def process_position_create_event(self, payload: PositionInCreate) -> None:
        await self.position_repo.process_create_position(payload)

    async def process_user_update_event(self, payload: UserInUpdate):
        await self.user_repo.process_update_user(payload)

    async def process_position_update_available(self, payload: PositionInUpdateAvailable):
        await self.position_repo.process_update_position_available_by_id(payload)

    async def process_position_update(self, payload: PositionInUpdate):
        await self.position_repo.process_update_position_by_id(payload)

    async def process_user_assets_record_create(self, payload: UserAssetsRecordInCreate):
        await self.user_assets_record_repo.process_create_user_assets_record(payload)

    async def process_user_assets_record_update(self, payload: UserAssetsRecordInUpdate):
        await self.user_assets_record_repo.process_update_user_assets_record(payload)

    async def pre_trade_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> PyDecimal:
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
        cash_needs = Decimal(order.quantity) * order.price.to_decimal() * (1 + user.commission.to_decimal())
        # 若用户现金可以满足订单需求
        if user.cash.to_decimal() >= cash_needs:
            # 冻结订单需要的现金
            frozen_cash = PyDecimal(user.cash.to_decimal() - cash_needs)
            payload = UserInUpdateCash(id=user.id, cash=frozen_cash)
            event = Event(USER_UPDATE_CASH_EVENT, payload)
            await self.event_engine.put(event)
            return frozen_cash
        else:
            raise InsufficientFunds

    async def __position_validation(
        self,
        order: OrderInCreate,
        user: UserInDB,
    ) -> PyDecimal:
        """用户持仓检查."""
        position = await self.position_repo.get_position(user.id, order.symbol, order.exchange)
        if position:
            if position.available_quantity >= order.quantity:
                event = Event(
                    POSITION_UPDATE_AVAILABLE_EVENT,
                    PositionInUpdateAvailable(
                        id=position.id,
                        available_quantity=position.available_quantity-order.quantity
                    )
                )
                await self.event_engine.put(event)
                return Decimal(order.quantity) * order.price.to_decimal()
            raise NotEnoughAvailablePositions
        else:
            raise NoPositionsAvailable

    async def create_position(self, order: OrderInDB) -> None:
        """新建持仓."""
        position = await self.position_repo.get_position(order.user, order.symbol, order.exchange)
        user = await self.user_repo.get_user_by_id(order.user)
        # 根据交易类别判断持仓股票可用数量
        order_available_quantity = order.traded_quantity if order.trade_type == TradeTypeEnum.T0 else 0
        # 交易费用
        fee = Decimal(order.quantity) * order.price.to_decimal() * user.commission.to_decimal()
        # 增持股票
        if position:
            quantity = position.quantity + order.traded_quantity
            current_price = order.trade_price
            # 持仓成本 = ((原持仓数 * 原持仓成本) + (订单交易数 * 订单交易价格)) / 持仓总量
            cost = ((Decimal(position.quantity) * position.cost.to_decimal()) +
                    (Decimal(order.traded_quantity) * order.trade_price.to_decimal())) / quantity
            available_quantity = position.available_quantity + order_available_quantity
            # 持仓利润 = (现交易价格 - 原持仓记录的价格) * 原持有数量 + 原利润 - 交易费用
            profit = (order.trade_price.to_decimal() - position.current_price.to_decimal()
                      ) * Decimal(position.quantity) + position.profit.to_decimal() - fee
            position_in_update = PositionInUpdate(
                id=position.id,
                quantity=quantity,
                current_price=current_price,
                cost=PyDecimal(cost),
                available_quantity=available_quantity,
                profit=PyDecimal(profit)
            )
            event = Event(POSITION_UPDATE_EVENT, position_in_update)
            await self.event_engine.put(event)
        # 建仓
        else:
            # 可用股票数量
            position_in_create = PositionInCreate(
                user=order.user,
                symbol=order.symbol,
                exchange=order.exchange,
                quantity=order.traded_quantity,
                available_quantity=order_available_quantity,
                cost=order.trade_price,
                current_price=order.trade_price,
                profit=-fee,
                first_buy_date=datetime.utcnow()
            )
            await self.event_engine.put(Event(POSITION_CREATE_EVENT, position_in_create))
            await self.update_user(order, position_in_create.quantity * position_in_create.current_price.to_decimal())

    async def reduce_position(self, order: OrderInDB) -> None:
        """减仓."""
        position = await self.position_repo.get_position(order.user, order.symbol, order.exchange)
        user = await self.user_repo.get_user_by_id(order.user)
        fee = Decimal(order.quantity) * order.price.to_decimal() * user.commission.to_decimal()
        quantity = position.quantity - order.traded_quantity
        current_price = order.trade_price
        tax = Decimal(order.quantity) * order.trade_price.to_decimal() * user.tax.to_decimal()
        # 持仓利润 = (现交易价格 - 原持仓记录的价格) * 原持仓数量 + 原持仓利润 - 交易费用 - 印花税
        profit = (order.trade_price.to_decimal() - position.current_price.to_decimal()
                  ) * Decimal(position.quantity) + position.profit.to_decimal() - fee - tax
        available_quantity = position.available_quantity - order.traded_quantity
        # 持仓成本 = ((原持仓量 * 原持仓价) - (订单交易量 * 订单交易价 * 交易费率)) / 持仓数量
        old_spent = Decimal(position.quantity) * position.cost.to_decimal()
        new_spent = Decimal(order.traded_quantity) * order.trade_price.to_decimal() * \
            (Decimal(1) - user.commission.to_decimal() - user.tax.to_decimal())
        cost = (old_spent - new_spent) / quantity if quantity else 0
        position_in_update = PositionInUpdate(
            id=position.id,
            quantity=quantity,
            current_price=current_price,
            cost=PyDecimal(cost),
            available_quantity=available_quantity,
            profit=PyDecimal(profit)
        )
        # 清仓
        if quantity == 0:
            position_in_update.last_sell_date = datetime.utcnow()
        event = Event(POSITION_UPDATE_EVENT, position_in_update)
        await self.event_engine.put(event)

    async def update_user(self, order: OrderInDB, securities_diff: Decimal) -> None:
        """订单成交后更新用户信息."""
        user = await self.user_repo.get_user_by_id(order.user)
        cost = Decimal(order.quantity) * order.trade_price.to_decimal() * (1 + user.commission.to_decimal())
        # 可用现金 = 原现金 + 预先冻结的现金 + 减实际花费的现金
        cash = user.cash.to_decimal() + order.amount.to_decimal() - cost
        # 证券资产 = 原证券资产 + 证券资产的变化值
        securities = user.securities.to_decimal() + securities_diff
        # 总资产 = 原资产 - 现金花费 + 证券资产变化值
        assets = user.assets.to_decimal() - cost + securities_diff
        user_in_update = UserInUpdate(id=user.id, cash=PyDecimal(cash), securities=PyDecimal(securities),
                                      assets=PyDecimal(assets))
        await self.event_engine.put(Event(USER_UPDATE_EVENT, user_in_update))

    async def on_liquidation(self, order: OrderInDB) -> None:
        """清算用户数据."""
        record = await self.user_assets_record_repo.get_user_assets_record_today()
        user = await self.user_repo.get_user_by_id(order.user)
        if record:
            record_in_update = UserAssetsRecordInUpdate(
                id=record.id, assets=user.assets, cash=user.cash, securities=user.securities
            )
            event = Event(USER_ASSETS_RECORD_UPDATE_EVENT, record_in_update)
            await self.event_engine.put(event)
        else:
            record_in_create = UserAssetsRecordInCreate(
                user=user.id, assets=user.assets, cash=user.cash, securities=user.securities, date=datetime.utcnow()
            )
            event = Event(USER_ASSETS_RECORD_CREATE_EVENT, record_in_create)
            await self.event_engine.put(event)

    async def on_position_liquidation(self) -> None:
        pass
