from typing import Any, Callable
from collections import defaultdict

from fastapi import BackgroundTasks


class Event:
    def __init__(self, type_: str, data: Any = None) -> None:
        self.type_ = type_
        self.data = data


HandlerType = Callable[[Event], None]


class EventEngine:
    def __init__(self) -> None:
        self._handlers = defaultdict(list)

    async def process(self, background_tasks: BackgroundTasks, event: Event) -> None:
        if event.type_ in self._handlers:
            for handler in self._handlers[event.type_]:
                background_tasks.add_task(handler, event)

    def register(self, type_: str, handler) -> None:
        handler_list = self._handlers[type_]
        if handler not in handler_list:
            handler_list.append(handler)

    def unregister(self, type_: str, handler: HandlerType) -> None:
        handler_list = self._handlers[type_]
        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type_)
