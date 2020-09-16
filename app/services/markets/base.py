from logging import INFO
from abc import ABC, abstractmethod

from app import settings
from app.models.schemas.log import Log
from app.services.engines.event_engine import Event, EventEngine
from app.services.quotes.base import BaseQuotes


class BaseMarket(ABC):
    def __init__(self, event_engine: EventEngine, quotes_api: BaseQuotes) -> None:
        self.event_engine = event_engine
        self._active = True
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
        self.quotes_api = quotes_api

    @abstractmethod
    def on_match(self) -> None:
        pass

    def write_log(self, msg: str, level: int = INFO) -> None:
        log = Log(log_content=msg, log_level=level)
        event = Event(settings.event_log, log)
        self.event_engine.put(event)
