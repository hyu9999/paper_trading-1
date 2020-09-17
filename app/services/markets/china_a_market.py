from app.models.domain.orders import OrderInDB
from app.models.enums import OrderTypeEnum, PriceTypeEnum
from app.services.engines.event_engine import EventEngine
from app.services.markets.base import BaseMarket
from app.services.quotes.base import BaseQuotes


class ChinaAMarket(BaseMarket):
    """A股市场."""
    def __init__(self, event_engine: EventEngine, quotes_api: BaseQuotes) -> None:
        super().__init__(event_engine, quotes_api)
        self.market_name = "china_a_market"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识

    def on_match(self) -> None:
        self.write_log(f"{self.market_name}交易市场已开启")

    def on_order_match(self, order: OrderInDB) -> None:
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
