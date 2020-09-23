from app.db.cache.entrust import EntrustCache
from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCache
from app.models.enums import OrderTypeEnum, PriceTypeEnum, OrderStatusEnum
from app.services.quotes.base import BaseQuotes
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.market_engine.base import BaseMarket


class ChinaAMarket(BaseMarket, BaseEngine):
    """A股市场."""
    def __init__(self, event_engine: EventEngine, quotes_api: BaseQuotes, entrust_cache: EntrustCache) -> None:
        super().__init__(event_engine, quotes_api)
        self.market_name = "china_a_market"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识
        self.entrust_cache = entrust_cache

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def register_event(self) -> None:
        pass

    async def on_order_arrived(self, order: OrderInDB) -> None:
        # 取消订单
        if order.order_type == OrderTypeEnum.CANCEL.value:
            pass
        # 清算订单
        elif order.order_type == OrderTypeEnum.LIQUIDATION.value:
            pass
        else:
            await self.exchange_validation(order)
            order.status = OrderStatusEnum.WAITING.value
            # TODO: 更新订单状态的事件
            await self.write_log(f"收到订单:{order.order_id}")
            order_in_cache_dict = dict(order)
            order_in_cache_dict.update({"price": str(order.price)})
            order_in_cache_dict.update({"order_id": str(order.order_id)})
            await self.entrust_cache.create_entrust(OrderInCache(**order_in_cache_dict))

    async def on_match(self) -> None:
        await self.write_log(f"{self.market_name}交易市场已开启")

    async def on_order_match(self, order: OrderInDB) -> None:
        quotes = self.quotes_api.get_ticks(order.stock_code)
        if order.order_type == OrderTypeEnum.BUY.value:
            # 涨停
            if quotes.ask1_p == 0:
                pass
                # TODO: 涨停处理
            # 市价成交
            if order.price_type == PriceTypeEnum.MARKET.value:
                order.order_price = quotes.ask1_p
                order.trade_price = quotes.ask1_p
                # TODO: 订单处理
            # 限价成交
            elif order.price_type == PriceTypeEnum.LIMIT.value:
                if order.order_price >= quotes.ask1_p:
                    order.trade_price = quotes.ask1_p
                    # TODO: 订单处理
        else:
            # 跌停
            if quotes.bid1_p == 0:
                pass
                # TODO: 跌停处理
            # 市价成交
            if order.price_type == PriceTypeEnum.MARKET.value:
                order.order_price = quotes.bid1_p,
                order.trade_price = quotes.bid1_p,
                # TODO: 订单处理
            # 限价成交
            elif order.price_type == PriceTypeEnum.LIMIT.value:
                if order.order_price <= quotes.bid1_p:
                    order.trade_price = quotes.bid1_p
                    # TODO: 订单处理
