from datetime import datetime
from typing import Optional

from pydantic import Field, PositiveInt

from app.models.base import DBModelMixin
from app.models.domain.stocks import Stock
from app.models.enums import (
    OrderStatusEnum,
    OrderTypeEnum,
    PriceTypeEnum,
    TradeTypeEnum,
)
from app.models.types import PyDecimal, PyObjectId


class Order(Stock):
    """订单基类."""

    volume: PositiveInt = Field(..., description="数量")
    price: PyDecimal = Field(..., description="价格")
    order_type: OrderTypeEnum = Field(..., description="订单类型")
    price_type: PriceTypeEnum = Field(..., description="价格类型")
    trade_type: TradeTypeEnum = Field(..., description="交易类型")


class OrderInDB(DBModelMixin, Order):
    """订单."""

    entrust_id: PyObjectId = Field(..., description="委托订单ID")  # 用于提供给外部系统的订单唯一标识符
    user: PyObjectId = Field(..., description="账户")
    status: OrderStatusEnum = Field(OrderStatusEnum.SUBMITTING, description="订单状态")
    traded_volume: int = Field(0, description="已成交数量")
    sold_price: Optional[PyDecimal] = Field(None, description="成交价格")
    order_date: datetime = Field(..., description="订单日期")
    frozen_amount: Optional[PyDecimal] = Field(None, description="冻结资金")
    frozen_stock_volume: Optional[int] = Field(None, description="冻结持仓股票数量")
    position_change: Optional[PyDecimal] = Field(None, description="仓位变化")
    deal_time: Optional[datetime] = Field(None, description="成交时间")
