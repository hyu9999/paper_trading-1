from datetime import timedelta, date

from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.rwmodel import RWModel, PyObjectId, PyDecimal
from app.models.enums import ExchangeEnum, OrderStatusEnum, OrderTypeEnum, PriceTypeEnum, TradeTypeEnum


class Order(DBModelMixin, RWModel):
    """订单"""
    user: PyObjectId = Field(..., description="账户")
    symbol: str = Field(..., description="股票代码")
    exchange: ExchangeEnum = Field(..., description="股票市场")
    quantity: int = Field(..., description="数量")
    price: PyDecimal = Field(..., description="价格")
    order_type: OrderTypeEnum = Field(..., description="订单类型")
    price_type: PriceTypeEnum = Field(..., description="价格类型")
    trade_type: TradeTypeEnum = Field(..., description="交易类型")

    status: OrderStatusEnum = Field(OrderStatusEnum.WAITING, description="订单状态")
    traded_quantity: int = Field(0, description="已成交数量")
    trade_price: PyDecimal = Field(0, description="交易价格")
    order_date: date = Field(..., description="订单日期")
    order_time: timedelta = Field(None, description="订单时长")

    @property
    def stock_code(self):
        return f"{self.symbol}.{self.exchange}"
