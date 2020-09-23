from aioredis import Redis


class BaseCache:

    def __init__(self, redis_db: Redis) -> None:
        self._cache = redis_db
