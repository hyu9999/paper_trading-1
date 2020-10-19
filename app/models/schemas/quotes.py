from datetime import datetime

from pydantic import Field

from app.models.types import PyDecimal
from app.models.domain.stocks import Stock
from app.models.schemas.rwschema import RWSchema


class Quotes(RWSchema, Stock):
    last_close: PyDecimal = Field(..., description="上一交易日收盘价")
    open: PyDecimal = Field(..., description="开盘价")
    high: PyDecimal = Field(..., description="当日最高价")
    low: PyDecimal = Field(..., description="当日最低价")
    # time: datetime = Field(..., description="时间")
    bid1_p: PyDecimal = Field(..., description="买1价格")
    bid2_p: PyDecimal = Field(..., description="买2价格")
    bid3_p: PyDecimal = Field(..., description="买3价格")
    bid4_p: PyDecimal = Field(..., description="买4价格")
    bid5_p: PyDecimal = Field(..., description="买5价格")
    ask1_p: PyDecimal = Field(..., description="卖1价格")
    ask2_p: PyDecimal = Field(..., description="卖2价格")
    ask3_p: PyDecimal = Field(..., description="卖3价格")
    ask4_p: PyDecimal = Field(..., description="卖4价格")
    ask5_p: PyDecimal = Field(..., description="卖5价格")
    bid1_v: int = Field(0, description="买1数量")
    bid2_v: int = Field(0, description="买2数量")
    bid3_v: int = Field(0, description="买3数量")
    bid4_v: int = Field(0, description="买4数量")
    bid5_v: int = Field(0, description="买5数量")
    ask1_v: int = Field(0, description="卖1数量")
    ask2_v: int = Field(0, description="卖1数量")
    ask3_v: int = Field(0, description="卖1数量")
    ask4_v: int = Field(0, description="卖1数量")
    ask5_v: int = Field(0, description="卖1数量")
