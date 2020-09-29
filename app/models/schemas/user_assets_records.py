from pydantic import Field

from app.models.types import PyDecimal, PyObjectId
from app.models.schemas.rwschema import RWSchema
from app.models.domain.user_assets_records import UserAssetsRecordInDB


class UserAssetsRecordInCreate(UserAssetsRecordInDB, RWSchema):
    pass


class UserAssetsRecordInUpdate(RWSchema):
    id: PyObjectId = Field(...)
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(..., description="证券资产")
