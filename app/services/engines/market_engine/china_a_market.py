from app.services.quotes.base import BaseQuotes
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.market_engine.base import BaseMarket


class ChinaAMarket(BaseMarket):
    """A股市场."""
    def __init__(self, event_engine: EventEngine, user_engine: UserEngine, quotes_api: BaseQuotes) -> None:
        super().__init__(event_engine, user_engine, quotes_api)
        self.market_name = "中国A股"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识
