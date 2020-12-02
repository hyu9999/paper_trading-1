from datetime import datetime, time

from hq2redis import HQ2Redis

from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.market_engine.base import BaseMarket


class ChinaAMarket(BaseMarket):
    """A股市场."""
    OPEN_MARKET_TIME = time(9, 30)   # 开市时间
    CLOSE_MARKET_TIME = time(15, 0)  # 闭市时间
    TRADING_PERIOD = [
        {"start": OPEN_MARKET_TIME, "end": time(11, 30)},
        {"start": time(13, 0), "end": CLOSE_MARKET_TIME}
    ]

    def __init__(self, event_engine: EventEngine, user_engine: UserEngine, quotes_api: HQ2Redis) -> None:
        super().__init__(event_engine, user_engine, quotes_api)
        self.market_name = "中国A股"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识

    @classmethod
    def is_trading_time(cls) -> bool:
        return True
        current_time = datetime.today().time()
        for period in cls.TRADING_PERIOD:
            if period["start"] <= current_time <= period["end"]:
                return True
        return False
