from datetime import date, datetime
from typing import List

from app import settings
from app.db.repositories.base import BaseRepository
from app.models.domain.statement import StatementInDB
from app.models.enums import TradeCategoryEnum
from app.models.types import PyObjectId


class StatementRepository(BaseRepository):
    """交割单仓库相关方法.

    Raises
    ------
    EntityDoesNotExist
        交割单不存在时触发
    """

    COLLECTION_NAME = settings.db.collections.statement

    async def create_statement(self, statement: StatementInDB) -> StatementInDB:
        statement_row = await self.collection.insert_one(statement.dict(exclude={"id"}))
        statement.id = statement_row.inserted_id
        return statement

    async def get_statement_list_by_symbol(
        self,
        user_id: PyObjectId,
        symbol: str,
    ) -> List[StatementInDB]:
        statement_rows = self.collection.find({"user": user_id, "symbol": symbol})
        return [StatementInDB(**statement) async for statement in statement_rows]

    async def get_statement_list(
        self,
        user_id: PyObjectId = None,
        start_date: date = None,
        end_date: date = None,
        trade_category: List[TradeCategoryEnum] = None,
        symbol: str = None,
    ) -> List[StatementInDB]:
        query = {}
        if user_id:
            query["user"] = user_id
        if start_date:
            start_date = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_date = datetime.combine(end_date, datetime.max.time())
        if not (start_date or end_date):
            date_query = None
        elif start_date and end_date:
            date_query = {"$gte": start_date, "$lt": end_date}
        elif start_date and not end_date:
            date_query = {"$gte": start_date}
        else:
            date_query = {"$lte": end_date}
        if date_query:
            query.update({"deal_time": date_query})
        if trade_category:
            query["trade_category"] = {"$in": [tc.value for tc in trade_category]}
        if symbol:
            query["symbol"] = symbol
        statement_rows = self.collection.find(query).sort("deal_time")
        return [StatementInDB(**statement) async for statement in statement_rows]
