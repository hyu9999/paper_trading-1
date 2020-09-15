from abc import ABC, abstractmethod


class Market(ABC):
    def __init__(self, event_engine) -> None:
        self.event_engine = event_engine
        self._active = True
        self.market_name = None         # 交易市场名称
        self.exchange_symbols = None    # 交易市场标识
