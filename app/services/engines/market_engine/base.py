import asyncio
from queue import Queue
from threading import Thread

from app.exceptions.service import InvalidExchange
from app.models.types import PyDecimal
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCache
from app.models.schemas.event_payload import LogPayload
from app.models.schemas.event_payload import OrderInUpdatePayload
from app.models.enums import OrderTypeEnum, PriceTypeEnum, OrderStatusEnum
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import Event, EventEngine
from app.services.engines.event_constants import (
    LOG_EVENT,
    ORDER_UPDATE_EVENT
)


class BaseMarket(BaseEngine):
    """交易引擎基类.

    Raises
    ------
    InvalidExchange
        订单指定的交易所不在于市场引擎规定的交易所列表中时触发
    """
    def __init__(self, event_engine: EventEngine) -> None:
        self.event_engine = event_engine
        self._active = True
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
        self.quotes_api = None
        self.entrust_queue = Queue()
        self._should_exit = asyncio.Event()
        self._process = Thread(target=self.matchmaking)

    def startup(self) -> None:
        self.write_log(f"[{self.market_name}]交易市场已开启.")
        self._process.start()

    def shutdown(self) -> None:
        self._should_exit.set()
        self._process.join()

    def register_event(self) -> None:
        pass

    def matchmaking(self) -> None:
        while not self._should_exit.is_set():
            if not self.entrust_queue.empty():
                order = self.entrust_queue.get()
                quotes = self.quotes_api.get_ticks(order.stock_code)
                if order.order_type == OrderTypeEnum.BUY.value:
                    # 涨停
                    if quotes.ask1_p == 0:
                        self.entrust_queue.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET.value:
                        order.price = quotes.ask1_p
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        self.update_order(order)
                        continue

                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT.value:
                        if PyDecimal(order.order_price) >= quotes.ask1_p:
                            order.trade_price = quotes.ask1_p
                            order.traded_quantity = order.quantity
                            self.update_order(order)
                        continue
                else:
                    # 跌停
                    if quotes.bid1_p == 0:
                        self.entrust_queue.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET.value:
                        order.price = quotes.ask1_p
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        self.update_order(order)
                        continue
                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT.value:
                        if PyDecimal(order.order_price) <= quotes.bid1_p:
                            order.trade_price = quotes.bid1_p
                            order.trade_price = quotes.ask1_p
                            order.traded_quantity = order.quantity
                            self.update_order(order)
                        continue

    def update_order(self, order: OrderInCache) -> None:
        """订单成交后的处理."""
        # 买入处理
        if order.order_type == OrderTypeEnum.BUY.value:
            # TODO: 买入处理
            pass
        elif order.order_type == OrderTypeEnum.SELL.value:
            # TODO: 卖出处理
            pass
        order.status = OrderStatusEnum.ALL_FINISHED.value \
            if order.quantity == order.traded_quantity \
            else OrderStatusEnum.PART_FINISHED.value
        order_in_update_payload = OrderInUpdatePayload(**dict(order))
        self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))

    def write_log(self, content: str, level: str = "INFO") -> None:
        payload = LogPayload(level=level, content=content)
        event = Event(LOG_EVENT, payload)
        self.event_engine.put(event)

    async def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
