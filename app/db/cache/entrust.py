import json

from app.db.cache.base import BaseCache
from app.models.schemas.orders import OrderInCache


class EntrustCache(BaseCache):
    async def push_entrust(self, order: OrderInCache) -> None:
        await self._cache.lpush("entrust", json.dumps(dict(order)))

    async def get_entrust(self) -> OrderInCache:
        order = await self._cache.rpop("entrust")
        if order:
            return OrderInCache(**json.loads(order))
