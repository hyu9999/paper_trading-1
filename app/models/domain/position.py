from datetime import datetime

from pydantic import Field

from app.models.base import DBModelMixin
from app.models.domain.stocks import Stock
from app.models.types import PyDecimal, PyObjectId


class Position(Stock):
    """持仓股票"""
    quantity: int = Field(..., description="持仓数量")
    available_quantity: int = Field(..., description="可卖数量")
    cost: PyDecimal = Field(..., description="持仓成本")
    current_price: PyDecimal = Field(..., description="当前价格")
    profit: PyDecimal = Field(..., description="利润")
    first_buy_date: datetime = Field(None, description="首次持有日期")
    last_sell_date: datetime = Field(None, description="最后卖出日期")


class PositionInDB(DBModelMixin, Position):
    user: PyObjectId = Field(..., description="用户ID")
