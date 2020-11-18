import asyncio

from hq2redis import HQ2Redis
from hq2redis.exceptions import EntityNotFound

from app.exceptions.service import InvalidExchange
from app.models.domain.statement import StatementInDB
from app.models.schemas.statement import StatementInCreateEvent
from app.models.types import PyDecimal
from app.models.base import get_utc_now
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInUpdate, OrderInUpdateStatus
from app.models.enums import OrderTypeEnum, PriceTypeEnum, OrderStatusEnum
from app.services.engines.base import BaseEngine
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import Event, EventEngine
from app.services.engines.market_engine.entrust_orders import EntrustOrders
from app.services.engines.event_constants import (
    ORDER_UPDATE_EVENT,
    EXIT_ENGINE_EVENT,
    ORDER_UPDATE_STATUS_EVENT,
    UNFREEZE_EVENT,
    STATEMENT_CREATE_EVENT,
)


class BaseMarket(BaseEngine):
    """交易引擎基类.

    Raises
    ------
    InvalidExchange
        订单指定的交易所不在于市场引擎规定的交易所列表中时触发
    """

    OPEN_MARKET_TIME = None   # 开市时间
    CLOSE_MARKET_TIME = None  # 闭市时间
    TRADING_PERIOD = None

    def __init__(self, event_engine: EventEngine, user_engine: UserEngine, quotes_api: HQ2Redis) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.user_engine = user_engine
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
        self.quotes_api = quotes_api
        self._entrust_orders = EntrustOrders()
        self._matchmaking_active = False

    async def startup(self) -> None:
        await self.register_event()
        if self.is_trading_time():
            await self.start_matchmaking()

    async def shutdown(self) -> None:
        await self._entrust_orders.put(EXIT_ENGINE_EVENT)

    async def start_matchmaking(self) -> None:
        if not self._matchmaking_active:
            self._matchmaking_active = True
            asyncio.create_task(self.matchmaking())
            await self.write_log(f"[{self.market_name}]交易市场已开启.")

    async def stop_matchmaking(self) -> None:
        if self._matchmaking_active:
            self._matchmaking_active = False
            await self._entrust_orders.put(EXIT_ENGINE_EVENT)
            await self.write_log(f"[{self.market_name}]交易市场已收盘.")

    async def register_event(self) -> None:
        pass

    async def put(self, order: OrderInDB) -> None:
        self.exchange_validation(order)
        payload = OrderInUpdateStatus(entrust_id=order.entrust_id, status=OrderStatusEnum.NOT_DONE)
        event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
        await self.event_engine.put(event)
        await self.write_log(f"收到新的委托订单[{order.order_type}]: `{order.entrust_id}`.")
        await self._entrust_orders.put(order)

    @staticmethod
    def is_trading_time() -> bool:
        pass

    async def matchmaking(self) -> None:
        while self._matchmaking_active:
            order = await self._entrust_orders.get()
            if order == EXIT_ENGINE_EVENT:
                continue
            # 取消委托订单
            if order.order_type == OrderTypeEnum.CANCEL:
                try:
                    del self._entrust_orders[str(order.entrust_id)]
                except KeyError:
                    await self.write_log(f"取消委托订单 `{order.entrust_id}` 失败, 该委托订单已处理.")
                    continue
                payload = OrderInUpdateStatus(entrust_id=order.entrust_id, status=OrderStatusEnum.CANCELED)
                update_order_status_event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
                await self.event_engine.put(update_order_status_event)
                unfreeze_event = Event(UNFREEZE_EVENT, order)
                await self.event_engine.put(unfreeze_event)
                await self.write_log(f"取消委托订单 `{order.entrust_id}` 成功.")
            else:
                try:
                    quotes = await self.quotes_api.get_stock_ticks(order.stock_code)
                except EntityNotFound:
                    await self.write_log(f"未找到股票 `{order.stock_code}` 的行情信息.")
                    continue
                if order.order_type == OrderTypeEnum.BUY:
                    # 涨停
                    if quotes.ask1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET:
                        order.price = PyDecimal(quotes.ask1_p)
                        order.sold_price = quotes.ask1_p
                        order.traded_volume = order.volume
                        await self.save_order(order)
                        continue
                    # 限价成交
                    else:
                        if order.price.to_decimal() >= quotes.ask1_p:
                            order.sold_price = PyDecimal(quotes.ask1_p)
                            order.traded_volume = order.volume
                            await self.save_order(order)
                        else:
                            await self._entrust_orders.put(order)
                        continue
                else:
                    # 跌停
                    if quotes.bid1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET:
                        order.price = quotes.ask1_p
                        order.sold_price = PyDecimal(quotes.ask1_p)
                        order.traded_volume = order.volume
                        await self.save_order(order)
                        continue
                    # 限价成交
                    else:
                        if order.price.to_decimal() <= quotes.bid1_p:
                            order.sold_price = PyDecimal(quotes.bid1_p)
                            order.traded_volume = order.volume
                            await self.save_order(order)
                        else:
                            await self._entrust_orders.put(order)
                        continue

    async def save_order(self, order: OrderInDB) -> None:
        """撮合完成后保存订单信息."""
        await self.write_log(f"委托订单 `{order.entrust_id}` 已撮合成交.")
        order.deal_time = get_utc_now()
        if order.order_type == OrderTypeEnum.BUY.value:
            securities_diff, costs = await self.user_engine.create_position(order)
        else:
            securities_diff, costs = await self.user_engine.reduce_position(order)
        order.status = OrderStatusEnum.ALL_FINISHED.value if order.volume == order.traded_volume \
            else OrderStatusEnum.PART_FINISHED.value
        order_in_update_payload = OrderInUpdate(**dict(order))
        user = await self.user_engine.user_repo.get_user_by_id(order.user)
        order_in_update_payload.position_change = PyDecimal(securities_diff / user.assets.to_decimal())
        await self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))
        statement_in_create = StatementInCreateEvent(costs=costs, order=order, securities_diff=securities_diff)
        await self.event_engine.put(Event(STATEMENT_CREATE_EVENT,statement_in_create ))

    def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
