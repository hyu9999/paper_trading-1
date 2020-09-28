from datetime import datetime

from pydantic import Field

from app.models.types import PyObjectId, PyDecimal
from app.models.schemas.rwschema import RWSchema
from app.models.domain.position import Position


class PositionInCreate(RWSchema, Position):
    user: PyObjectId = Field(..., description="用户ID")


class PositionInResponse(RWSchema, Position):
    pass


class PositionInUpdateAvailable(RWSchema):
    id: PyObjectId = Field(..., description="ID")
    available_quantity: int = Field(..., description="可卖数量")


class PositionInUpdate(RWSchema):
    id: PyObjectId = Field(..., description="ID")
    quantity: int = Field(..., description="持仓数量")
    available_quantity: int = Field(..., description="可卖数量")
    cost: PyDecimal = Field(..., description="持仓成本")
    current_price: PyDecimal = Field(..., description="当前价格")
    profit: PyDecimal = Field(..., description="利润")
    last_sell_date: datetime = Field(None, description="最后卖出日期")


class PositionInDelete(RWSchema):
    id: PyObjectId = Field(..., description="ID")
