from pydantic import Field

from app.models.base import PyObjectId
from app.models.domain.orders import Order
from app.models.enums import PriceTypeEnum
from app.models.schemas.rwschema import RWSchema


class OrderInCreate(RWSchema, Order):
    price_type: PriceTypeEnum = Field(None, description="价格类型")


class OrderInCreateViewResponse(RWSchema, Order):
    order_id: PyObjectId = Field(..., description="订单ID")


class OrderInCache(RWSchema):
    symbol: str = Field(..., description="股票代码")
    exchange: str = Field(..., description="股票市场")
    quantity: int = Field(..., description="数量")
    price: str = Field(..., description="价格")
    order_id: str = Field(..., description="订单ID")
    order_type: str = Field(..., description="订单类型")
    price_type: str = Field(..., description="价格类型")
    trade_type: str = Field(..., description="交易类型")
