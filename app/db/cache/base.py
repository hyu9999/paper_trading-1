from aioredis import Redis


class BaseCache:
    DB = None
    LIST_KEY = None

    def __init__(self, redis_pool: Redis) -> None:
        assert redis_pool.db == self.DB, "请传入正确的Redis连接池."
        self._cache = redis_pool
