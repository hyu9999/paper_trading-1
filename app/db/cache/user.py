from typing import List, Optional

from fastapi.encoders import jsonable_encoder

from app import settings
from app.db.cache.base import BaseCache
from app.exceptions.db import EntityDoesNotExist
from app.models.schemas.users import UserInCache
from app.models.types import PyObjectId


class UserCache(BaseCache):
    DB = settings.redis.user_db
    USER_KEY = "user_{user_id}"
    USER_KEY_PREFIX = "user_"
    IS_RELOAD_KEY = "is_reload"

    @property
    async def is_reload(self) -> bool:
        is_reload = await self._cache.get(self.IS_RELOAD_KEY) == "1"
        if is_reload:
            await self._cache.set(self.IS_RELOAD_KEY, "0")
        return is_reload

    async def update_user(
        self,
        user: UserInCache,
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ) -> None:
        key = self.USER_KEY.format(user_id=user.id)
        if await self._cache.exists(key):
            await self._cache.hmset_dict(
                self.USER_KEY.format(user_id=user.id),
                jsonable_encoder(user, include=include, exclude=exclude),
            )

    async def set_user(
        self,
        user: UserInCache,
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ) -> None:
        await self._cache.hmset_dict(
            self.USER_KEY.format(user_id=user.id),
            jsonable_encoder(user, include=include, exclude=exclude),
        )

    async def set_user_many(self, user_list: List[UserInCache]) -> None:
        pipeline = self._cache.pipeline()
        for user in user_list:
            pipeline.hmset_dict(
                self.USER_KEY.format(user_id=user.id), jsonable_encoder(user)
            )
        await pipeline.execute()

    async def get_user_by_id(self, user_id: PyObjectId) -> UserInCache:
        user = await self._cache.hgetall(self.USER_KEY.format(user_id=user_id))
        if not user:
            raise EntityDoesNotExist
        return UserInCache(**user)

    async def get_all_user(self) -> List[UserInCache]:
        pipeline = self._cache.pipeline()
        for user_id in await self.get_keys(self.USER_KEY_PREFIX + "*"):
            pipeline.hgetall(user_id)
        return [UserInCache(**user) for user in await pipeline.execute()]
