from pydantic import Field

from app.models.rwmodel import RWModel
from app.models.mixin import DBModelMixin


class Account(DBModelMixin, RWModel):
    """账户"""
    assets: float = Field(..., description="总资产")
    available: float = Field(..., description="可用资金")
    market: float = Field(..., description="总市值")
    capital: float = Field(..., description="初始资金")
    commission: float = Field(..., description="佣金")
    tax: float = Field(..., description="税金")
    slippage: float = Field(..., description="滑点")
    desc: str = Field("", description="账户描述")
