from pydantic import Field

from app.models.domain.users import User
from app.models.schemas.rwschema import RWSchema


class UserInCreate(RWSchema):
    capital: float = Field(..., description="初始资金")
    desc: str = Field("", description="账户描述")


class UserInLogin(RWSchema):
    id: str = Field(..., description="用户ID")


class UserInResponse(RWSchema, User):
    token: str

