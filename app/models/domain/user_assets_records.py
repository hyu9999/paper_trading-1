from datetime import datetime

from pydantic import Field

from app.models.domain.rwmodel import RWModel
from app.models.types import PyDecimal, PyObjectId
from app.models.base import DBModelMixin, get_utc_now


class UserAssetsRecordInDB(DBModelMixin, RWModel):
    user: PyObjectId = Field(..., description="用户")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(..., description="证券资产")
    date: datetime = Field(..., description="日期")
    check_time: datetime = Field(default_factory=get_utc_now, description="检查时间")
