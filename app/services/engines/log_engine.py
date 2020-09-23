from loguru import logger

from app import settings
from app.models.schemas.event_payload import LogPayload
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine
from app.services.engines.event_constants import LOG_EVENT


class LogEngine(BaseEngine):
    def __init__(self, event_engine: EventEngine):
        self.level = settings.log.level
        self.event_engine = event_engine

    async def startup(self) -> None:
        await self.register_event()

    async def shutdown(self) -> None:
        pass

    async def register_event(self, *args, **kwargs) -> None:
        await self.event_engine.register(LOG_EVENT, self.process_log_event)

    def process_log_event(self, payload: LogPayload) -> None:
        logger.log(self.level, payload.content)
