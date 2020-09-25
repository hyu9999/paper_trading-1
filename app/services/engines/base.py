from abc import ABC, abstractmethod

from app.models.schemas.log import Log
from app.services.engines.event_engine import Event
from app.services.engines.event_constants import LOG_EVENT


class BaseEngine(ABC):
    def __init__(self):
        self.event_engine = None

    @abstractmethod
    async def startup(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def shutdown(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def register_event(self, *args, **kwargs) -> None:
        pass

    async def write_log(self, content: str, level: str = "INFO") -> None:
        payload = Log(level=level, content=content)
        event = Event(LOG_EVENT, payload)
        await self.event_engine.put(event)
