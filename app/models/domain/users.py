from typing import Optional

from pydantic import Field
from bson import Decimal128

from app.models.types import PyDecimal
from app.models.base import DBModelMixin
from app.models.domain.rwmodel import RWModel


class User(RWModel):
    capital: PyDecimal = Field(..., description="初始资金")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(Decimal128("0.00"), description="证券资产")
    commission: PyDecimal = Field(Decimal128("0.0003"), description="佣金")
    tax_rate: PyDecimal = Field(Decimal128("0.001"), description="税点")
    slippage: PyDecimal = Field(Decimal128("0.01"), description="滑点")
    desc: Optional[str] = Field(None, description="账户描述")


class UserInDB(DBModelMixin, User):
    """用户"""
    pass
