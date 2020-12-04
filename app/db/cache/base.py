from typing import List

from aioredis import Redis


class BaseCache:
    DB = None
    PAGE_SIZE = 500

    def __init__(self, redis_pool: Redis) -> None:
        assert redis_pool.db == self.DB, "请传入正确的Redis连接池."
        self._cache = redis_pool

    async def get_keys(self, match: str = None) -> List[str]:
        _, keys = await self._cache.scan(cursor=0, match=match, count=self.PAGE_SIZE)
        return keys

    async def delete_key(self, key: str) -> None:
        await self._cache.delete(key)
