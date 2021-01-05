from datetime import datetime
from typing import Optional

from bson import Decimal128
from pydantic import Field, validator

from app.models.base import DBModelMixin, get_utc_now
from app.models.domain.stocks import Stock
from app.models.types import PyDecimal, PyObjectId


class DividendRecords(Stock):
    """分红记录."""

    user: PyObjectId = Field(..., description="账户")
    cash: Optional[PyDecimal] = Field(None, description="现金红利")
    volume: int = Field(0, description="股票红利")
    timestamp: datetime = Field(default_factory=get_utc_now)

    @validator("cash", pre=True)
    def set_cash_default(cls, v):
        if not v:
            return Decimal128("0")
        return v

    @validator("volume", pre=True)
    def set_volume_default(cls, v):
        if not v:
            return 0
        return v


class DividendRecordsInDB(DBModelMixin, DividendRecords):
    ...
