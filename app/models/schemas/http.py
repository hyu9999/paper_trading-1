from pydantic import Field

from app.models.schemas.rwschema import RWSchema


class HttpMessage(RWSchema):
    text: str = Field(..., description="消息文本")
