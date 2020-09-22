from abc import ABC, abstractmethod


class BaseEngine(ABC):
    @abstractmethod
    async def startup(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def shutdown(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def register_event(self, *args, **kwargs) -> None:
        pass
