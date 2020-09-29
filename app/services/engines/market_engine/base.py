import asyncio
from typing import Union
from collections import OrderedDict, deque

from app.exceptions.service import InvalidExchange
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInUpdate, OrderInUpdateStatus
from app.models.enums import OrderTypeEnum, PriceTypeEnum, OrderStatusEnum, EntrustOrdersMode
from app.services.quotes.base import BaseQuotes
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import Event, EventEngine
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_constants import (
    ORDER_UPDATE_EVENT,
    EXIT_ENGINE_EVENT,
    ORDER_UPDATE_STATUS_EVENT)


class EntrustOrders(OrderedDict):
    def __init__(self, mode: EntrustOrdersMode = EntrustOrdersMode.TIME_PRIORITY):
        super().__init__()
        # Futures.
        self._waiters = deque()
        self.mode = mode
        self.loop = asyncio.get_event_loop()

    def empty(self):
        return not self

    def _wakeup_next(self):
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    async def get(self, *args, **kwargs) -> Union[OrderInDB, Event]:
        while self.empty():
            waiter = self.loop.create_future()
            self._waiters.append(waiter)
            await waiter
        return self.popitem(last=False)[1]

    async def put(self, item: Union[OrderInDB, Event]) -> None:
        if isinstance(item, OrderInDB):
            self[item.order_id] = item
        else:
            self["event"] = item
        self._wakeup_next()


class BaseMarket(BaseEngine):
    """交易引擎基类.

    Raises
    ------
    InvalidExchange
        订单指定的交易所不在于市场引擎规定的交易所列表中时触发
    """
    def __init__(self, event_engine: EventEngine, user_engine: UserEngine, quotes_api: BaseQuotes) -> None:
        super().__init__()
        self.event_engine = event_engine
        self.user_engine = user_engine
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
        self.quotes_api = quotes_api
        self._entrust_orders = EntrustOrders()
        self._should_exit = asyncio.Event()

    async def startup(self) -> None:
        asyncio.create_task(self.matchmaking())
        await self.write_log(f"[{self.market_name}]交易市场已开启.")

    async def shutdown(self) -> None:
        self._should_exit.set()
        await self._entrust_orders.put(EXIT_ENGINE_EVENT)

    async def register_event(self) -> None:
        pass

    async def put(self, order: OrderInDB) -> None:
        await self.exchange_validation(order)
        payload = OrderInUpdateStatus(order_id=order.order_id, status=OrderStatusEnum.WAITING)
        event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
        await self.event_engine.put(event)
        await self.write_log(f"收到新订单: [{order.order_id}].")
        await self._entrust_orders.put(order)

    async def matchmaking(self) -> None:
        while not self._should_exit.is_set():
            order = await self._entrust_orders.get()
            if order == EXIT_ENGINE_EVENT:
                continue
            # 取消委托订单
            if order.order_type == OrderTypeEnum.CANCEL:
                payload = OrderInUpdateStatus(order_id=order.order_id, status=OrderStatusEnum.CANCELED)
                event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
                await self.event_engine.put(event)
            # 清算委托订单
            elif order.order_type == OrderTypeEnum.LIQUIDATION:
                continue
            else:
                quotes = await self.quotes_api.get_ticks(order.stock_code)
                if order.order_type == OrderTypeEnum.BUY.value:
                    # 涨停
                    if quotes.ask1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET.value:
                        order.price = quotes.ask1_p
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        await self.save_order(order)
                        continue

                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT.value:
                        if order.price.to_decimal() >= quotes.ask1_p.to_decimal():
                            order.trade_price = quotes.ask1_p
                            order.traded_quantity = order.quantity
                            await self.save_order(order)
                        continue
                else:
                    # 跌停
                    if quotes.bid1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET.value:
                        order.price = quotes.ask1_p
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        await self.save_order(order)
                        continue
                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT.value:
                        if order.price.to_decimal() <= quotes.bid1_p.to_decimal():
                            order.trade_price = quotes.bid1_p
                            order.traded_quantity = order.quantity
                            await self.save_order(order)
                        continue

    async def save_order(self, order: OrderInDB) -> None:
        """撮合完成后保存订单信息."""
        # 买入处理
        if order.order_type == OrderTypeEnum.BUY.value:
            await self.user_engine.create_position(order)
        elif order.order_type == OrderTypeEnum.SELL.value:
            await self.user_engine.reduce_position(order)
        order.status = OrderStatusEnum.ALL_FINISHED.value \
            if order.quantity == order.traded_quantity \
            else OrderStatusEnum.PART_FINISHED.value
        order_in_update_payload = OrderInUpdate(**dict(order))
        await self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))

    async def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
