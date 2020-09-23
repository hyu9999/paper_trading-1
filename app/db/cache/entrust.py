import json

from app.db.cache.base import BaseCache
from app.models.schemas.orders import OrderInCache


class EntrustCache(BaseCache):
    async def create_entrust(self, order: OrderInCache) -> None:
        await self._cache.lpush("entrust", json.dumps(dict(order)))
