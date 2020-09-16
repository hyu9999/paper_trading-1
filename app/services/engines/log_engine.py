from loguru import logger

from app import settings
from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine, Event


class LogEngine(BaseEngine):
    def __init__(self, event_engine: EventEngine) -> None:
        super().__init__(event_engine=event_engine)
        self.engine_name = "log"
        if not settings.log.active:
            return
        self.register_event()

    def register_event(self) -> None:
        self.event_engine.register(settings.service.event_log, self.process_log_event)

    @staticmethod
    def process_log_event(event: Event) -> None:
        log = event.data
        logger.log(log.level, log.msg)

    def close(self) -> None:
        pass
