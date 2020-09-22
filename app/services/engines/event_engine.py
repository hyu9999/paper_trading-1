import asyncio
from typing import Any, Callable
from collections import defaultdict


class Event:
    def __init__(self, type_: str, data: Any = None) -> None:
        self.type_ = type_
        self.data = data


HandlerType = Callable[[Event], None]


class EventEngine:
    def __init__(self) -> None:
        self._handlers = defaultdict(list)
        self._event_queue = asyncio.Queue()
        self._should_exit = asyncio.Event()

    async def main(self) -> None:
        loop = asyncio.get_event_loop()
        while not self._should_exit.is_set():
            event = await self._event_queue.get()
            print(self._handlers)
            print(event.type_)
            print([handler for handler in self._handlers[event.type_]])
            [loop.run_in_executor(None, handler, event) for handler in self._handlers[event.type_]
             if event.type_ in self._handlers]

    async def startup(self) -> None:
        asyncio.create_task(self.main())

    async def shutdown(self) -> None:
        self._should_exit.set()

    async def put(self, event: Event):
        await self._event_queue.put(event)

    async def register(self, type_: str, handler: callable) -> None:
        handler_list = self._handlers[type_]
        if handler not in handler_list:
            handler_list.append(handler)

    async def unregister(self, type_: str, handler: HandlerType) -> None:
        handler_list = self._handlers[type_]
        if handler in handler_list:
            handler_list.remove(handler)
