import asyncio

from app.exceptions.service import InvalidExchange
from app.models.types import PyDecimal
from app.models.base import get_utc_now
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInUpdate, OrderInUpdateStatus
from app.models.enums import OrderTypeEnum, PriceTypeEnum, OrderStatusEnum
from app.services.quotes.base import BaseQuotes
from app.services.engines.base import BaseEngine
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import Event, EventEngine
from app.services.engines.market_engine.entrust_orders import EntrustOrders
from app.services.engines.event_constants import (
    ORDER_UPDATE_EVENT,
    EXIT_ENGINE_EVENT,
    ORDER_UPDATE_STATUS_EVENT,
    MARKET_CLOSE_EVENT,
    UNFREEZE_EVENT,
)


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
        await self.register_event()
        asyncio.create_task(self.matchmaking())
        await self.write_log(f"[{self.market_name}]交易市场已开启.")

    async def shutdown(self) -> None:
        self._should_exit.set()
        await self._entrust_orders.put(EXIT_ENGINE_EVENT)

    async def register_event(self) -> None:
        pass

    async def put(self, order: OrderInDB) -> None:
        self.exchange_validation(order)
        payload = OrderInUpdateStatus(entrust_id=order.entrust_id, status=OrderStatusEnum.NOT_DONE)
        event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
        await self.event_engine.put(event)
        await self.write_log(f"收到新的委托订单: [{order.entrust_id}].")
        await self._entrust_orders.put(order)

    @staticmethod
    def is_trading_time() -> bool:
        pass

    async def matchmaking(self) -> None:
        while not self._should_exit.is_set():
            if not self.is_trading_time():
                await self.shutdown()
                market_close_event = Event(MARKET_CLOSE_EVENT)
                await self.event_engine.put(market_close_event)
                await self.write_log(f"[{self.market_name}]交易市场已收盘.")
            order = await self._entrust_orders.get()
            if order == EXIT_ENGINE_EVENT:
                continue
            # 取消委托订单
            if order.order_type == OrderTypeEnum.CANCEL:
                payload = OrderInUpdateStatus(entrust_id=order.entrust_id, status=OrderStatusEnum.CANCELED)
                update_order_status_event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
                await self.event_engine.put(update_order_status_event)
                unfreeze_event = Event(UNFREEZE_EVENT, order)
                await self.event_engine.put(unfreeze_event)
            else:
                quotes = await self.quotes_api.get_ticks(order.stock_code)
                if order.order_type == OrderTypeEnum.BUY:
                    # 涨停
                    if quotes.ask1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET:
                        order.price = quotes.ask1_p
                        order.sold_price = quotes.ask1_p
                        order.traded_volume = order.volume
                        await self.save_order(order)
                        continue

                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT:
                        if order.price.to_decimal() >= quotes.ask1_p.to_decimal():
                            order.sold_price = quotes.ask1_p
                            order.traded_volume = order.volume
                            await self.save_order(order)
                        continue
                else:
                    # 跌停
                    if quotes.bid1_p == 0:
                        await self._entrust_orders.put(order)
                        continue

                    # 市价成交
                    if order.price_type == PriceTypeEnum.MARKET:
                        order.price = quotes.ask1_p
                        order.sold_price = quotes.ask1_p
                        order.traded_volume = order.volume
                        await self.save_order(order)
                        continue

                    # 限价成交
                    elif order.price_type == PriceTypeEnum.LIMIT:
                        if order.price.to_decimal() <= quotes.bid1_p.to_decimal():
                            order.sold_price = quotes.bid1_p
                            order.traded_volume = order.volume
                            await self.save_order(order)
                        continue

    async def save_order(self, order: OrderInDB) -> None:
        """撮合完成后保存订单信息."""
        order.deal_time = get_utc_now()
        if order.order_type == OrderTypeEnum.BUY.value:
            securities_diff = await self.user_engine.create_position(order)
        elif order.order_type == OrderTypeEnum.SELL.value:
            securities_diff = await self.user_engine.reduce_position(order)
        else:
            securities_diff = 0
        order.status = OrderStatusEnum.ALL_FINISHED.value \
            if order.volume == order.traded_volume \
            else OrderStatusEnum.PART_FINISHED.value
        order_in_update_payload = OrderInUpdate(**dict(order))
        user = await self.user_engine.user_repo.get_user_by_id(order.user)
        order_in_update_payload.position_change = PyDecimal(securities_diff / user.assets.to_decimal())
        await self.event_engine.put(Event(ORDER_UPDATE_EVENT, order_in_update_payload))

    def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
