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

    def startup(self) -> None:
        self.register_event()

    def shutdown(self) -> None:
        pass

    def register_event(self, *args, **kwargs) -> None:
        self.event_engine.register(LOG_EVENT, self.process_log_event)

    @staticmethod
    def process_log_event(payload: LogPayload) -> None:
        logger.log(payload.level, payload.content)
