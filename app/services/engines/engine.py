import logging
from typing import Type

from app import settings
from app.services.engines.account_engine import AccountEngine
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.log_engine import LogEngine
from app.models.schemas.log import Log
from app.services.quotes.tdx import TDXQuotes


class MainEngine:
    def __init__(self, event_engine: EventEngine = None) -> None:
        self.event_engine = event_engine if event_engine else EventEngine()
        self.engines = {}
        self.quotes_api = None      # 行情API
        self.event_engine.start()
        self.init_engines()

    def add_engine(self, engine_class: Type[BaseEngine]) -> BaseEngine:
        """注册事件并把事件实例加到self.engines中"""
        engine = engine_class(event_engine=self.event_engine, main_engine=self)
        self.engines[engine.engine_name] = engine
        return engine

    def init_engines(self) -> None:
        """初始化引擎，把指定的引擎实例化"""
        self.add_engine(LogEngine)
        self.add_engine(AccountEngine)

    def start(self) -> None:
        self.write_log("模拟交易主引擎：启动")
        self.set_quotes_api()

    def write_log(self, msg: str, level: int = logging.INFO) -> None:
        log = Log(msg=msg, level=level)
        event = Event(settings.event_log, log)
        self.event_engine.put(event)

    def set_quotes_api(self) -> None:
        """设置行情源"""
        tdx = TDXQuotes()
        tdx.connect_pool()
        self.quotes_api = tdx

