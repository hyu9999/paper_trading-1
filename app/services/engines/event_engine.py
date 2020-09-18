import asyncio
from time import perf_counter
from typing import Any, Callable
from collections import defaultdict


class Event:
    def __init__(self, type_: str, data: Any = None) -> None:
        self.type_ = type_
        self.data = data


HandlerType = Callable[[Event], None]


class EventEngine:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._handlers = defaultdict(list)
        self._tasks = None

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def put(self, event: Event) -> None:
        await self._queue.put(event)
        await self._run()

    async def _run(self) -> None:
        if not self._queue.empty():
            event = await self._queue.get()
            await self._process(event)

    async def _process(self, event: Event) -> None:
        print("任务开始运行...")
        start = perf_counter()
        if event.type_ in self._handlers:
            tasks = [asyncio.create_task(handler(event)) for handler in self._handlers[event.type_]]
            await asyncio.gather(*tasks)
        stop = perf_counter()
        print(f"3次任务共用时{stop - start}s")

    async def register(self, type_: str, handler) -> None:
        handler_list = self._handlers[type_]
        if handler not in handler_list:
            handler_list.append(handler)

    async def unregister(self, type_: str, handler: HandlerType) -> None:
        handler_list = self._handlers[type_]
        if handler in handler_list:
            handler_list.remove(handler)

        if not handler_list:
            self._handlers.pop(type_)
