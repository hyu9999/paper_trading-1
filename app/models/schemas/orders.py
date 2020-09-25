from pydantic import Field

from app.models.base import PyObjectId
from app.models.types import PyDecimal
from app.models.domain.orders import Order
from app.models.schemas.rwschema import RWSchema
from app.models.enums import PriceTypeEnum, OrderStatusEnum


class OrderInCreate(RWSchema, Order):
    price_type: PriceTypeEnum = Field(None, description="价格类型")


class OrderInCreateViewResponse(RWSchema, Order):
    order_id: PyObjectId = Field(..., description="订单ID")


class OrderInResponse(RWSchema, Order):
    order_id: PyObjectId = Field(..., description="订单ID")
    status: OrderStatusEnum = Field(OrderStatusEnum.SUBMITTING, description="订单状态")


class OrderInUpdate(RWSchema):
    order_id: PyObjectId = Field(...)
    price: PyDecimal = Field(..., description="价格")
    status: OrderStatusEnum = Field(..., description="订单状态")
    traded_quantity: int = Field(..., description="已成交数量")
    trade_price: PyDecimal = Field(..., description="交易价格")


class OrderInUpdateStatus(RWSchema):
    order_id: PyObjectId = Field(...)
    status: OrderStatusEnum = Field(..., description="订单状态")
