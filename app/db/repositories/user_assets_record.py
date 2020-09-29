from datetime import datetime

from app import settings
from app.db.repositories.base import BaseRepository
from app.models.domain.user_assets_records import UserAssetsRecordInDB
from app.models.schemas.user_assets_records import UserAssetsRecordInCreate, UserAssetsRecordInUpdate


class UserAssetsRecordRepository(BaseRepository):
    """用户资产记录相关方法.

    函数名称以process开头的为事件处理专用函数.
    """
    COLLECTION_NAME = settings.db.collections.user_assets_record

    async def get_user_assets_record_today(self):
        record_row = await self.collection.find_one(
            {"datetime": datetime.combine(datetime.utcnow(), datetime.min.time())}
        )
        return UserAssetsRecordInDB(**record_row)

    async def process_create_user_assets_record(self, record: UserAssetsRecordInCreate):
        record_in_db = UserAssetsRecordInDB(
            **record.dict(),
            datetime=datetime.combine(record.date, datetime.min.time())
        )
        await self.collection.insert_one(record_in_db.dict(exclude={"id"}))

    async def process_update_user_assets_record(self, record: UserAssetsRecordInUpdate):
        await self.collection.update_one({"_id": record.id}, {"$set": record.dict(exclude={"id", })})
