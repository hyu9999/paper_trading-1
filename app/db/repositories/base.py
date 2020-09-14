from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


class BaseRepository:
    COLLECTION_NAME = None

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[self.COLLECTION_NAME]

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self._collection
