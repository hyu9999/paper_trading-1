from datetime import datetime

from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.rwmodel import RWModel
from app.models.types import PyDecimal, PyObjectId


class UserAssetsRecordInDB(DBModelMixin, RWModel):
    user: PyObjectId = Field(..., description="用户")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(..., description="证券资产")
    date: datetime = Field(..., description="日期")
    check_time: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
