import asyncio
from typing import Any, Callable
from collections import defaultdict


class Event:
    def __init__(self, type_: str, data: Any = None) -> None:
        """事件.

        Parameters
        ----------
        type_ : 事件类型
        data : 用于process的参数
        """
        self.type_ = type_
        self.data = data


HandlerType = Callable[[Event], None]


class EventEngine:
    """事件引擎.

    Attributes
    ----------
    _handlers : 存放事件对应的handler列表
    _event_queue : 事件队列
    _should_exit : 是否应该退出，用于控制事件引擎运行状态

    Examples
    ----------
    >>> from app.services.engines.event_engine import Event, EventEngine
    >>> event_engine = EventEngine()
    >>> EXAMPLES_EVENT = "example_event"
    >>> example_event = Event(EXAMPLES_EVENT, data="Hello Event.")
    >>> def example_process(event: Event):
    ...     print(event.data)
    ...
    >>> await event_engine.startup()
    >>> await event_engine.register(EXAMPLES_EVENT, example_process)
    >>> await event_engine.put(example_event)
    Hello Event.
    >>> await event_engine.shutdown()
    """
    def __init__(self) -> None:
        self._handlers = defaultdict(list)
        self._event_queue = asyncio.Queue()
        self._should_exit = asyncio.Event()

    async def main(self, loop: asyncio.AbstractEventLoop) -> None:
        while not self._should_exit.is_set():
            event = await self._event_queue.get()
            [loop.run_in_executor(None, handler, event) for handler in self._handlers[event.type_]
             if event.type_ in self._handlers]

    async def startup(self) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.main(loop))

    async def shutdown(self) -> None:
        self._should_exit.set()

    async def put(self, event: Event) -> None:
        await self._event_queue.put(event)

    async def register(self, type_: str, handler: callable) -> None:
        handler_list = self._handlers[type_]
        if handler not in handler_list:
            handler_list.append(handler)

    async def unregister(self, type_: str, handler: HandlerType) -> None:
        handler_list = self._handlers[type_]
        if handler in handler_list:
            handler_list.remove(handler)
