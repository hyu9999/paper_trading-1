from datetime import datetime, time

from hq2redis import HQ2Redis

from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.market_engine.base import BaseMarket


class ChinaAMarket(BaseMarket):
    """A股市场."""
    def __init__(self, event_engine: EventEngine, user_engine: UserEngine, quotes_api: HQ2Redis) -> None:
        super().__init__(event_engine, user_engine, quotes_api)
        self.market_name = "中国A股"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识

    @staticmethod
    def is_trading_time() -> bool:
        return True
        current_time = datetime.today().time()
        trading_period = [{"start": time(9, 20), "end": time(11, 30)}, {"start": time(13, 0), "end": time(15, 0)}]
        for period in trading_period:
            if period["start"] <= current_time <= period["end"]:
                return True
        return False
