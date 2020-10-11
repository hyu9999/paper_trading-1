import asyncio
from typing import Union
from collections import OrderedDict, deque

from app.models.domain.orders import OrderInDB
from app.models.enums import EntrustOrdersMode
from app.services.engines.event_engine import Event


class EntrustOrders(OrderedDict):
    def __init__(self, mode: EntrustOrdersMode = EntrustOrdersMode.TIME_PRIORITY):
        super().__init__()
        # Futures.
        self._waiters = deque()
        self.mode = mode
        self.loop = asyncio.get_event_loop()

    def empty(self):
        return not self

    def _wakeup_next(self):
        while self._waiters:
            waiter = self._waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    def get_all(self):
        return self.values()

    async def get(self, *args, **kwargs) -> Union[OrderInDB, Event]:
        while self.empty():
            waiter = self.loop.create_future()
            self._waiters.append(waiter)
            await waiter
        return self.popitem(last=False)[1]

    async def put(self, item: Union[OrderInDB, Event]) -> None:
        if isinstance(item, OrderInDB):
            self[str(item.entrust_id)] = item
        else:
            self["event"] = item
        self._wakeup_next()
