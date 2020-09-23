import asyncio
from logging import INFO

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
    ORDER_UPDATE_STATUS_EVENT,
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
        self.entrust_cache = None
        self._should_exit = asyncio.Event()

    async def startup(self) -> None:
        asyncio.create_task(self.matchmaking())
        await self.write_log(f"{self.market_name}交易市场已开启.")

    async def shutdown(self) -> None:
        self._should_exit.set()

    async def register_event(self) -> None:
        pass

    async def matchmaking(self) -> None:
        while not self._should_exit.is_set():
            order = await self.entrust_cache.get_entrust()
            quotes = self.quotes_api.get_ticks(order.stock_code)
            if order.order_type == OrderTypeEnum.BUY.value:
                # 涨停
                if quotes.ask1_p == 0:
                    await self.entrust_cache.push_entrust(order)
                    continue

                # 市价成交
                if order.price_type == PriceTypeEnum.MARKET.value:
                    order.price = quotes.ask1_p
                    order.trade_price = quotes.ask1_p
                    order.traded_quantity = order.quantity
                    await self.update_order(order)
                    continue

                # 限价成交
                elif order.price_type == PriceTypeEnum.LIMIT.value:
                    if PyDecimal(order.order_price) >= quotes.ask1_p:
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        await self.update_order(order)
                    continue
            else:
                # 跌停
                if quotes.bid1_p == 0:
                    await self.entrust_cache.push_entrust(order)
                    continue

                # 市价成交
                if order.price_type == PriceTypeEnum.MARKET.value:
                    order.price = quotes.ask1_p
                    order.trade_price = quotes.ask1_p
                    order.traded_quantity = order.quantity
                    await self.update_order(order)
                    continue
                # 限价成交
                elif order.price_type == PriceTypeEnum.LIMIT.value:
                    if PyDecimal(order.order_price) <= quotes.bid1_p:
                        order.trade_price = quotes.bid1_p
                        order.trade_price = quotes.ask1_p
                        order.traded_quantity = order.quantity
                        await self.update_order(order)
                    continue

    async def update_order(self, order: OrderInCache) -> None:
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
        await self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))

    async def write_log(self, content: str, level: int = INFO) -> None:
        payload = LogPayload(level=level, content=content)
        event = Event(LOG_EVENT, payload)
        await self.event_engine.put(event)

    async def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
