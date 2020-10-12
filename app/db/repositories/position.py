from typing import List, Optional
from datetime import datetime

from app import settings
from app.db.repositories.base import BaseRepository
from app.models.types import PyObjectId, PyDecimal
from app.models.enums import ExchangeEnum
from app.models.domain.position import PositionInDB
from app.models.schemas.position import PositionInCreate
from app.models.schemas.position import (
    PositionInResponse,
    PositionInUpdateAvailable,
    PositionInUpdate,
)


class PositionRepository(BaseRepository):
    """持仓仓库相关方法.

    函数名称以process开头的为事件处理专用函数.

    Raises
    ------
    EntityDoesNotExist
        用户无持仓记录时触发
    """
    COLLECTION_NAME = settings.db.collections.position

    async def create_position(
        self,
        *,
        user: PyObjectId,
        symbol: str,
        exchange: ExchangeEnum,
        volume: int,
        available_volume: int,
        cost: PyDecimal,
        current_price: PyDecimal,
        profit: PyDecimal,
        first_buy_date: datetime,
        last_sell_date: Optional[datetime]
    ) -> PositionInDB:
        position = PositionInDB(user=user, symbol=symbol, exchange=exchange, volume=volume,
                                available_volume=available_volume, cost=cost, current_price=current_price,
                                profit=profit, first_buy_date=first_buy_date, last_sell_date=last_sell_date)
        position_row = await self.collection.insert_one(position.dict(exclude={"id"}))
        position.id = position_row.inserted_id
        return position

    async def get_position_by_id(self, position_id: PyObjectId) -> PositionInDB:
        position_row = await self.collection.find_one({"_id": position_id})
        return PositionInDB(**position_row)

    async def get_position(self, user_id: PyObjectId, symbol: str, exchange: ExchangeEnum) -> PositionInDB:
        position_row = await self.collection.find_one({"user": user_id, "symbol": symbol, "exchange": exchange.value})
        return PositionInDB(**position_row) if position_row else None

    async def get_positions_by_user_id(self, user_id: PyObjectId) -> List[PositionInResponse]:
        position_rows = self.collection.find({"user": user_id})
        return [PositionInResponse(**position) async for position in position_rows]

    async def process_create_position(self, position: PositionInCreate) -> None:
        position_in_db = PositionInDB(**position.dict())
        await self.collection.insert_one(position_in_db.dict(exclude={"id"}))

    async def process_update_position_available_by_id(self, position: PositionInUpdateAvailable) -> None:
        await self.collection.update_one(
            {"_id": position.id},
            {"$set": {"available_volume": position.available_volume}}
        )

    async def process_update_position(self, position: PositionInUpdate) -> None:
        await self.collection.update_one({"_id": position.id}, {"$set": position.dict(exclude={"id"})})
