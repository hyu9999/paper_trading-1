from logging import INFO
from abc import ABC, abstractmethod

from app import settings
from app.exceptions.service import InvalidExchange
from app.models.schemas.log import Log
from app.models.domain.orders import OrderInDB
from app.services.quotes.base import BaseQuotes
from app.services.engines.event_engine import Event, EventEngine


class BaseMarket(ABC):
    """交易引擎基类.

    Raises
    ------
    InvalidExchange
        订单指定的交易所不在于市场引擎规定的交易所列表中时触发
    """
    def __init__(self, event_engine: EventEngine, quotes_api: BaseQuotes) -> None:
        self.event_engine = event_engine
        self._active = True
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
        self.quotes_api = quotes_api

    @abstractmethod
    async def on_match(self) -> None:
        pass

    async def write_log(self, msg: str, level: int = INFO) -> None:
        log = Log(msg=msg, level=level)
        event = Event(settings.service.event_log, log)
        await self.event_engine.put(event)

    async def exchange_validation(self, order: OrderInDB) -> None:
        """交易市场类别检查."""
        if order.exchange not in self.exchange_symbols:
            raise InvalidExchange
