from app.services.markets.base import Market


class ChinaAMarket(Market):
    """A股市场"""
    def __init__(self, event_engine) -> None:
        super().__init__(event_engine)
        self.market_name = "china_a_market"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识
