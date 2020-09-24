from typing import List

from app import settings
from app.db.repositories.base import BaseRepository
from app.exceptions.db import EntityDoesNotExist
from app.models.types import PyObjectId
from app.models.enums import ExchangeEnum
from app.models.domain.position import PositionInDB
from app.models.schemas.position import (
    PositionInResponse,
    PositionInUpdateAvailable,
    PositionInUpdate,
    PositionInDelete
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

    async def get_position_by_user_id(self, user_id: PyObjectId) -> PositionInDB:
        position_row = await self.collection.find_one({"user": user_id})
        if position_row:
            return PositionInDB(**position_row)
        raise EntityDoesNotExist(f"用户`{user_id}`无持仓记录.")

    async def get_position(self, user_id: PyObjectId, symbol: str, exchange: ExchangeEnum) -> PositionInDB:
        position_row = await self.collection.find_one({"user": user_id, "symbol": symbol, "exchange": exchange.value})
        return PositionInDB(**position_row) if position_row else None

    async def get_positions_by_user_id(self, user_id: PyObjectId) -> List[PositionInResponse]:
        position_rows = self.collection.find({"user": user_id})
        return [PositionInResponse(**position) async for position in position_rows]

    def process_create_position(self, position: PositionInDB) -> None:
        self.collection.insert_one(position.dict(exclude={"id"}))

    def process_update_position_available_by_id(self, position: PositionInUpdateAvailable) -> None:
        self.collection.update_one({"id": position.id}, {"set": {"available_quantity": position.available_quantity}})

    def process_update_position_by_id(self, position: PositionInUpdate) -> None:
        self.collection.update_one({"id": position.id}, {"set": position.dict(exclude={"id"})})

    def process_delete_position_by_id(self, position: PositionInDelete) -> None:
        self.collection.delete_one({"id": position.id})
