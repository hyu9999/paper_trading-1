from app import settings
from app.db.repositories.base import BaseRepository

from app.errors.db import EntityDoesNotExist
from app.models.domain.users import User
from app.models.base import PyObjectId


class UsersRepository(BaseRepository):
    COLLECTION_NAME = settings.db.collections.user

    async def create_user(self, *, capital: float, desc: str) -> User:
        user = User(capital=capital, desc=desc, assets=capital, cash=capital)
        user_row = await self.collection.insert_one(user.dict(exclude={"id"}))
        user.id = user_row.inserted_id
        return user

    async def get_user_by_id(self, *, _id: PyObjectId) -> User:
        user_row = await self.collection.find_one({"_id": _id})
        if user_row:
            return User(**user_row)
        raise EntityDoesNotExist(f"ID为[{_id}]的用户未找到.")
