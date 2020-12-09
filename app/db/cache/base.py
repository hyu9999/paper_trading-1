from collections.abc import AsyncIterable
from typing import List

from aioredis import Redis


class BaseCache:
    DB = None

    def __init__(self, redis_pool: Redis) -> None:
        assert redis_pool.db == self.DB, "请传入正确的Redis连接池."
        self._cache = redis_pool

    async def scan_iter(self, match: str = None, count: int = None) -> AsyncIterable:
        cursor = "0"
        while cursor != 0:
            cursor, keys = await self._cache.scan(
                cursor=cursor, match=match, count=count
            )
            yield keys

    async def get_keys(self, match: str = None) -> List[str]:
        # return list(
        #     itertools.chain.from_iterable(
        #         [keys async for keys in self.scan_iter(match=match)]
        #     )
        # )
        return await self._cache.keys(match)

    async def delete_key(self, key: str) -> None:
        await self._cache.delete(key)
