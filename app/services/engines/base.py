from abc import ABC, abstractmethod


class BaseEngine(ABC):
    @abstractmethod
    def startup(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def shutdown(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def register_event(self, *args, **kwargs) -> None:
        pass
