from typing import List, Optional

from pydantic import Field, validator

from app.models.domain.users import User, UserInDB
from app.models.schemas.rwschema import RWSchema
from app.models.types import PyDecimal, PyObjectId


class UserInCreate(RWSchema, User):
    capital: Optional[PyDecimal] = Field(..., description="初始资金")

    @validator("capital")
    def capital_must_greater_than_0(cls, v):
        if v and v.to_decimal() <= 0:
            raise ValueError("账户初始资金必须大于0.")
        return v

    @validator("capital")
    def set_capital_default(cls, v):
        if not v:
            return PyDecimal("1000000")
        return v


class UserInLogin(RWSchema):
    id: PyObjectId = Field(..., description="用户ID")


class UserInResponse(RWSchema, UserInDB):
    token: Optional[str]


class ListOfUserInResponse(RWSchema):
    users: List[User]
    count: int


class UserInUpdate(RWSchema):
    id: PyObjectId = Field(...)
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(0.00, description="证券资产")


class UserInUpdateCash(RWSchema):
    cash: PyDecimal = Field(..., description="现金")

    @validator("cash")
    def validate_cash(self, v):
        if v.to_decimal() < 0:
            raise ValueError("用户取款金额超出账户可用金额.")
        return v


class UserInCache(RWSchema):
    id: PyObjectId = Field(..., alias="_id")
    capital: PyDecimal = Field(..., description="初始资产")
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    available_cash: Optional[PyDecimal] = Field(None, description="可用现金")
    securities: PyDecimal = Field(..., description="证券资产")
    commission: PyDecimal = Field(..., description="佣金")
    tax_rate: PyDecimal = Field(..., description="税点")

    @validator("available_cash", pre=True, always=True)
    def set_available_cash_default(cls, v, values):
        if v is None:
            v = values["cash"]
        return v
