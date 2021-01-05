from app import settings
from app.db.repositories.base import BaseRepository
from app.models.domain.dividend_records import DividendRecordsInDB


class DividendRecordsRepository(BaseRepository):

    COLLECTION_NAME = settings.db.collections.dividend_records

    async def create_dividend_records(
        self, dividend_records: DividendRecordsInDB
    ) -> DividendRecordsInDB:
        dividend_records_row = await self.collection.insert_one(
            dividend_records.dict(exclude={"id"})
        )
        dividend_records.id = dividend_records_row.inserted_id
        return dividend_records
