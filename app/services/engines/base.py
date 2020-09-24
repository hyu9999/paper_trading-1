from abc import ABC, abstractmethod

from app.models.schemas.log import Log
from app.services.engines.event_engine import Event
from app.services.engines.event_constants import LOG_EVENT


class BaseEngine(ABC):
    def __init__(self):
        self.event_engine = None

    @abstractmethod
    def startup(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def shutdown(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def register_event(self, *args, **kwargs) -> None:
        pass

    def write_log(self, content: str, level: str = "INFO") -> None:
        payload = Log(level=level, content=content)
        event = Event(LOG_EVENT, payload)
        self.event_engine.put(event)
