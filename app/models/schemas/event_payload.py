from pydantic import Field

from app.models.enums import OrderStatusEnum
from app.models.domain.orders import OrderInDB
from app.models.schemas.rwschema import RWSchema
from app.models.types import PyObjectId, PyDecimal


class BasePayload(RWSchema):
    pass


class LogPayload(BasePayload):
    content: str
    level: str


class UserInUpdateCashPayload(BasePayload):
    id: PyObjectId = Field(...)
    cash: PyDecimal = Field(..., description="现金")


class OrderInCreatePayload(BasePayload, OrderInDB):
    pass


class OrderInUpdatePayload(BasePayload):
    order_id: PyObjectId = Field(...)
    price: PyDecimal = Field(..., description="价格")
    status: OrderStatusEnum = Field(..., description="订单状态")
    traded_quantity: int = Field(..., description="已成交数量")
    trade_price: PyDecimal = Field(..., description="交易价格")


class OrderInUpdateStatusPayload(BasePayload):
    id: PyObjectId = Field(...)
    status: OrderStatusEnum = Field(..., description="订单状态")
