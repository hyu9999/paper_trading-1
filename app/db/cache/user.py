from typing import List

from fastapi.encoders import jsonable_encoder

from app import settings
from app.db.cache.base import BaseCache
from app.exceptions.db import EntityDoesNotExist
from app.models.schemas.users import UserInCache
from app.models.types import PyObjectId


class UserCache(BaseCache):
    DB = settings.redis.user_db
    LIST_KEY = "user_list"

    async def get_user_id_list(self) -> List[str]:
        return await self._cache.smembers(self.LIST_KEY)

    async def set_user(self, user: UserInCache) -> None:
        await self._cache.hmset_dict(str(user.id), jsonable_encoder(user))
        await self._cache.sadd(self.LIST_KEY, str(user.id))

    async def set_user_many(self, user_list: List[UserInCache]) -> None:
        pipeline = self._cache.pipeline()
        [pipeline.hmset_dict(str(user.id), jsonable_encoder(user)) for user in user_list]
        pipeline.sadd(self.LIST_KEY, *[str(user.id) for user in user_list])
        await pipeline.execute()

    async def get_user_by_id(self, user_id: PyObjectId) -> UserInCache:
        user = await self._cache.hgetall(str(user_id))
        if not user:
            raise EntityDoesNotExist
        return UserInCache(**user)

    async def get_all_user(self) -> List[UserInCache]:
        pipeline = self._cache.pipeline()
        [pipeline.hgetall(user_id) for user_id in await self.get_user_id_list()]
        return [UserInCache(**user) for user in await pipeline.execute()]

    async def update_user(self, user_id: PyObjectId) -> UserInCache:
        pass
