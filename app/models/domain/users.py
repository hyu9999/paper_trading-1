from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.rwmodel import RWModel


class User(DBModelMixin, RWModel):
    """用户"""
    capital: float = Field(1000000.00, description="初始资金")
    assets: float = Field(..., description="总资产")
    cash: float = Field(..., description="现金")
    securities: float = Field(0.00, description="证券资产")
    commission: float = Field(0.0003, description="佣金")
    tax: float = Field(0.001, description="税金")
    slippage: float = Field(0.01, description="滑点")
    desc: str = Field("", description="账户描述")
