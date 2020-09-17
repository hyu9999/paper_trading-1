import logging
from typing import Type

from app import settings
from app.models.schemas.log import Log
from app.services.engines.account_engine import AccountEngine
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.log_engine import LogEngine
# from app.services.markets.constant import MARKET_NAME_MAPPING
from app.services.quotes.tdx import TDXQuotes


class Engine(BaseEngine):
    def __init__(self, event_engine: EventEngine = None) -> None:
        super().__init__(event_engine)
        self.event_engine = event_engine if event_engine else EventEngine()
        self.engines = {}
        self.quotes_api = None
        self._market = None
        self.event_engine.start()
        # self.init_engines()

    def add_engine(self, engine_class: Type[BaseEngine]) -> BaseEngine:
        """注册事件并把事件实例加到self.engines中"""
        engine = engine_class(event_engine=self.event_engine)
        self.engines[engine.engine_name] = engine
        return engine

    def init_engines(self) -> None:
        """初始化引擎，把指定的引擎实例化"""
        self.add_engine(LogEngine)
        self.add_engine(AccountEngine)

    def start(self) -> None:
        pass
        # self.set_quotes_api()
        # self._market = MARKET_NAME_MAPPING[settings.service.market](self.event_engine, self.quotes_api)

    def write_log(self, msg: str, level: int = logging.INFO) -> None:
        log = Log(msg=msg, level=level)
        event = Event(settings.service.event_log, log)
        self.event_engine.put(event)

    def set_quotes_api(self) -> None:
        """设置行情源"""
        tdx = TDXQuotes()
        tdx.connect_pool()
        self.quotes_api = tdx

    def close(self) -> None:
        self.event_engine.stop()
        for engine in self.engines.values():
            engine.close()
