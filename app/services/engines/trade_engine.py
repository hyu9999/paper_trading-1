import asyncio
from typing import Type

from app.services.engines.event_engine import Event, EventEngine


class TradeEngine:
    PROCESS_EVENT = "process event"

    def __init__(self, event_engine: Type[EventEngine] = None) -> None:
        self.event_engine = event_engine() if event_engine else EventEngine()

    async def start(self):
        await self.event_engine.start()
        await self.register_event()

    async def stop(self):
        await self.event_engine.stop()

    async def on_foo(self, background_tasks):
        event = Event(type_=self.PROCESS_EVENT, data=None)
        background_tasks.add_task(self.event_engine.put, event)

    async def register_event(self):
        await self.event_engine.register(self.PROCESS_EVENT, self.process1)
        await self.event_engine.register(self.PROCESS_EVENT, self.process2)
        await self.event_engine.register(self.PROCESS_EVENT, self.process3)

    @staticmethod
    async def process1(*args) -> None:
        print("process1 start")
        await asyncio.sleep(10)
        print("process1 done")

    @staticmethod
    async def process2(*args) -> None:
        print("process2 start")
        await asyncio.sleep(15)
        print("process2 done")

    @staticmethod
    async def process3(*args) -> None:
        print("process3 start")
        await asyncio.sleep(20)
        print("process3 done")
