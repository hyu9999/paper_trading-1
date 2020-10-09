from pydantic import Field

from app.models.base import PyObjectId
from app.models.types import PyDecimal
from app.models.domain.orders import Order
from app.models.schemas.rwschema import RWSchema
from app.models.enums import PriceTypeEnum, OrderStatusEnum


class OrderInCreate(RWSchema, Order):
    price_type: PriceTypeEnum = Field(None, description="价格类型")


class OrderInCreateViewResponse(RWSchema, Order):
    entrust_id: PyObjectId = Field(..., description="委托订单ID")


class OrderInResponse(RWSchema, Order):
    entrust_id: PyObjectId = Field(..., description="委托订单ID")
    status: OrderStatusEnum = Field(OrderStatusEnum.SUBMITTING, description="订单状态")


class OrderInUpdate(RWSchema):
    entrust_id: PyObjectId = Field(...)
    price: PyDecimal = Field(..., description="价格")
    status: OrderStatusEnum = Field(..., description="订单状态")
    traded_volume: int = Field(..., description="已成交数量")
    sold_price: PyDecimal = Field(..., description="交易价格")


class OrderInUpdateStatus(RWSchema):
    entrust_id: PyObjectId = Field(...)
    status: OrderStatusEnum = Field(..., description="订单状态")
