from abc import ABC, abstractmethod

from app.models.schemas.quotes import Quotes


class BaseQuotes(ABC):

    @abstractmethod
    def get_ticks(self, code: str) -> Quotes:
        pass

    def connect_pool(self) -> None:
        pass
