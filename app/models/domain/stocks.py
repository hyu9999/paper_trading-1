from pydantic import Field

from app.models.domain.rwmodel import RWModel
from app.models.enums import ExchangeEnum


class Stock(RWModel):
    symbol: str = Field(..., description="股票代码")
    exchange: ExchangeEnum = Field(..., description="股票市场")
