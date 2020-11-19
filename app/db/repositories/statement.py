from app import settings
from app.db.repositories.base import BaseRepository
from app.models.domain.statement import StatementInDB


class StatementRepository(BaseRepository):
    """交割单仓库相关方法.

    Raises
    ------
    EntityDoesNotExist
        交割单不存在时触发
    """
    COLLECTION_NAME = settings.db.collections.statement

    async def create_statement(
        self,
        statement: StatementInDB
    ) -> StatementInDB:
        statement_row = await self.collection.insert_one(statement.dict(exclude={"id"}))
        statement.id = statement_row.inserted_id
        return statement
