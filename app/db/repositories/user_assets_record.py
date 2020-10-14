from typing import List
from datetime import datetime, date

from app import settings
from app.db.repositories.base import BaseRepository
from app.models.base import get_utc_now
from app.models.types import PyObjectId
from app.models.domain.user_assets_records import UserAssetsRecordInDB
from app.models.schemas.user_assets_records import UserAssetsRecordInCreate, UserAssetsRecordInUpdate


class UserAssetsRecordRepository(BaseRepository):
    """用户资产记录相关方法.

    函数名称以process开头的为事件处理专用函数.
    """
    COLLECTION_NAME = settings.db.collections.user_assets_record

    async def get_user_assets_records(
        self,
        user_id: PyObjectId,
        record_date: date
    ) -> List[UserAssetsRecordInDB]:
        query = {}
        if user_id:
            query["user"] = user_id
        if record_date:
            query["date"] = datetime.combine(record_date, datetime.min.time())
        records_row = self.collection.find(query)
        return [UserAssetsRecordInDB(**record) async for record in records_row]

    async def get_user_assets_record_today(self, user_id: PyObjectId):
        record_row = await self.collection.find_one(
            {"date": datetime.combine(get_utc_now(), datetime.min.time()), "user": user_id}
        )
        if record_row:
            return UserAssetsRecordInDB(**record_row)

    async def process_create_user_assets_record(self, record: UserAssetsRecordInCreate):
        record.date = datetime.combine(record.date, datetime.min.time())
        record_in_db = UserAssetsRecordInDB(
            **record.dict(),
        )
        await self.collection.insert_one(record_in_db.dict(exclude={"id"}))

    async def process_update_user_assets_record(self, record: UserAssetsRecordInUpdate):
        await self.collection.update_one({"_id": record.id}, {"$set": record.dict(exclude={"id"})})
