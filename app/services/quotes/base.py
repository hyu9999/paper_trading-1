from abc import ABC, abstractmethod

from app.models.schemas.quotes import Quotes


class BaseQuotes(ABC):

    @abstractmethod
    async def get_ticks(self, code: str) -> Quotes:
        pass

    async def connect_pool(self) -> None:
        pass
