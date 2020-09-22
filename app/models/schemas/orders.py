from pydantic import Field

from app.models.base import PyObjectId
from app.models.domain.orders import Order
from app.models.enums import PriceTypeEnum
from app.models.schemas.rwschema import RWSchema


class OrderInCreate(RWSchema, Order):
    price_type: PriceTypeEnum = Field(None, description="价格类型")


class OrderInCreateResponse(RWSchema, Order):
    order_id: PyObjectId = Field(..., description="订单ID")
