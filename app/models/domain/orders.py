from datetime import timedelta, datetime

from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.stocks import Stock
from app.models.types import PyObjectId, PyDecimal
from app.models.enums import OrderStatusEnum, OrderTypeEnum, PriceTypeEnum, TradeTypeEnum


class Order(Stock):
    """订单基类."""
    quantity: int = Field(..., description="数量")
    price: PyDecimal = Field(..., description="价格")
    order_type: OrderTypeEnum = Field(..., description="订单类型")
    price_type: PriceTypeEnum = Field(..., description="价格类型")
    trade_type: TradeTypeEnum = Field(..., description="交易类型")


class OrderInDB(DBModelMixin, Order):
    """订单."""
    order_id: PyObjectId = Field(..., description="订单ID")  # 用于提供给外部系统的订单唯一标识符
    user: PyObjectId = Field(..., description="账户")
    status: OrderStatusEnum = Field(OrderStatusEnum.SUBMITTING, description="订单状态")
    traded_quantity: int = Field(0, description="已成交数量")
    trade_price: PyDecimal = Field(0, description="交易价格")
    order_date: datetime = Field(..., description="订单日期")
    order_time: timedelta = Field(None, description="订单时长")
    turnover: PyDecimal = Field(..., description="成交额")
