from pydantic import Field

from app.models.base import DBModelMixin
from app.models.types import PyDecimal
from app.models.domain.rwmodel import RWModel


class User(RWModel):
    capital: PyDecimal = Field(1000000.00, description="初始资金")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(0.00, description="证券资产")
    commission: PyDecimal = Field(0.0003, description="佣金")
    tax: PyDecimal = Field(0.001, description="税金")
    slippage: PyDecimal = Field(0.01, description="滑点")
    desc: str = Field("", description="账户描述")


class UserInDB(DBModelMixin, User):
    """用户"""
    pass

