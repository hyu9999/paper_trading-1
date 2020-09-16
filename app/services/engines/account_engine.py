from app.services.engines.base import BaseEngine
from app.services.engines.event_engine import EventEngine


class AccountEngine(BaseEngine):
    def __init__(self, event_engine: EventEngine) -> None:
        super().__init__(event_engine)
        self.engine_name = "account"
        self.event_register()

    def event_register(self) -> None:
        pass

    def close(self) -> None:
        pass

    def load_data(self):
        pass
