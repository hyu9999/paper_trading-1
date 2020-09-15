from abc import ABC, abstractmethod

from app.services.engines.event_engine import EventEngine
from app.services.engines import MainEngine


class BaseEngine(ABC):
    def __init__(
        self,
        event_engine: EventEngine,
        main_engine: MainEngine = None,
    ) -> None:
        self.event_engine = event_engine
        self.engine_name = None

    @abstractmethod
    def close(self) -> None:
        pass
