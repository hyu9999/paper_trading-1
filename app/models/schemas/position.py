from pydantic import Field

from app.models.types import PyObjectId, PyDecimal
from app.models.schemas.rwschema import RWSchema
from app.models.domain.position import PositionInDB, Position


class PositionInCreate(RWSchema, PositionInDB):
    pass


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


class PositionInDelete(RWSchema):
    id: PyObjectId = Field(..., description="ID")
