from pydantic import Field, PositiveInt

from app.models.base import DBModelMixin
from app.models.domain.stocks import Stock
from app.models.enums import TradeTypeEnum
from app.models.domain.rwmodel import RWModel
from app.models.types import PyDecimal, PyObjectId


class Costs(RWModel):
    """费用."""
    total: PyDecimal = Field(..., description="费用合计")
    commission: PyDecimal = Field(..., description="佣金")
    tax: PyDecimal = Field(..., description="印花税")


class Statement(Stock):
    """交割单."""
    entrust_id: PyObjectId = Field(..., description="委托单ID")
    user: PyObjectId = Field(..., description="账户")
    trade_type: TradeTypeEnum = Field(..., description="交易类型")
    volume: PositiveInt = Field(..., description="成交数量")
    sold_price: PyDecimal = Field(..., description="成交价格")
    amount: PyDecimal = Field(..., description="发生金额")
    costs: Costs = Field(..., description="费用")


class StatementInDB(DBModelMixin, Statement):
    """交割单."""
    pass
