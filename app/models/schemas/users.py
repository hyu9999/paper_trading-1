from typing import List, Optional

from pydantic import Field

from app.models.domain.users import User
from app.models.schemas.rwschema import RWSchema
from app.models.types import PyDecimal, PyObjectId


class UserInCreate(RWSchema):
    capital: PyDecimal = Field(..., description="初始资金")
    desc: Optional[str] = Field(description="账户描述")


class UserInLogin(RWSchema):
    id: PyObjectId = Field(..., description="用户ID")


class UserInResponse(RWSchema, User):
    token: str


class ListOfUserInResponse(RWSchema):
    users: List[User]
    count: int


class UserInUpdateCash(RWSchema):
    id: PyObjectId = Field(...)
    cash: PyDecimal = Field(..., description="现金")


class UserInUpdate(RWSchema):
    id: PyObjectId = Field(...)
    assets: PyDecimal = Field(..., description="总资产")
    cash: PyDecimal = Field(..., description="现金")
    securities: PyDecimal = Field(0.00, description="证券资产")
