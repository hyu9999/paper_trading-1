from typing import Optional

from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.rwmodel import RWModel
from app.models.enums import UserStatusEnum
from app.models.types import PyDecimal


class User(RWModel):
    capital: PyDecimal = Field(..., description="初始资金")
    assets: PyDecimal = Field("1000000", description="总资产")
    cash: PyDecimal = Field("1000000", description="现金")
    securities: PyDecimal = Field("0.00", description="证券资产")
    commission: PyDecimal = Field("0.0003", description="佣金")
    tax_rate: PyDecimal = Field("0.001", description="税点")
    slippage: PyDecimal = Field("0.01", description="滑点")
    desc: Optional[str] = Field(None, description="账户描述")


class UserInDB(DBModelMixin, User):
    """用户"""

    securities: PyDecimal = Field(..., description="证券资产")
    commission: PyDecimal = Field(..., description="佣金")
    tax_rate: PyDecimal = Field(..., description="税点")
    slippage: PyDecimal = Field(..., description="滑点")
    status: Optional[UserStatusEnum] = Field(None, description="用户状态")
