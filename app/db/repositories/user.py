from typing import List

from pymongo import UpdateOne

from app import settings
from app.db.repositories.base import BaseRepository
from app.exceptions.db import EntityDoesNotExist
from app.models.domain.users import UserInDB
from app.models.enums import UserStatusEnum
from app.models.schemas.users import UserInCache, UserInCreate, UserInUpdate
from app.models.types import PyObjectId


class UserRepository(BaseRepository):
    """用户仓库相关方法.

    函数名称以process开头的为事件处理专用函数.

    Raises
    ------
    EntityDoesNotExist
        用户不存在时触发
    """

    COLLECTION_NAME = settings.db.collections.user

    async def create_user(self, user_in_create: UserInCreate) -> UserInDB:
        user = UserInDB(**user_in_create.dict())
        user.assets = user.capital
        user.cash = user.capital
        user_row = await self.collection.insert_one(user.dict(exclude={"id"}))
        user.id = user_row.inserted_id
        return user

    async def get_user_by_id(self, user_id: PyObjectId) -> UserInDB:
        user_row = await self.collection.find_one({"_id": user_id})
        if user_row:
            return UserInDB(**user_row)
        raise EntityDoesNotExist(f"用户`{str(user_id)}`不存在.")

    async def get_user_list(self) -> List[UserInDB]:
        return [UserInDB(**user) async for user in self.collection.find({})]

    async def get_user_list_to_cache(self) -> List[UserInCache]:
        return [
            UserInCache(**user)
            async for user in self.collection.find(
                {"status": {"$ne": UserStatusEnum.TERMINATED}}
            )
        ]

    async def update_user(self, user: UserInUpdate) -> None:
        await self.collection.update_one(
            {"_id": user.id}, {"$set": user.dict(exclude={"id"})}
        )

    async def terminate_user(self, user_id: PyObjectId) -> None:
        await self.collection.update_one(
            {"_id": user_id}, {"$set": {"status": UserStatusEnum.TERMINATED}}
        )

    async def bulk_update(self, options: List[UpdateOne]) -> None:
        await self.collection.bulk_write(options)

    async def process_update_user(
        self, user: UserInUpdate, exclude: list = None
    ) -> None:
        exclude_field = ["id"]
        if exclude:
            exclude_field.extend(exclude)
        await self.collection.update_one(
            {"_id": user.id}, {"$set": user.dict(exclude=set(exclude_field))}
        )
