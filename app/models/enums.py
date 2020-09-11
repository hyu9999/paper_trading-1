from enum import Enum, unique


@unique
class ExchangeEnum(Enum):
    """股票市场"""
    SH = "SH"
    SZ = "SZ"


@unique
class OrderTypeEnum(Enum):
    """订单类型"""
    BUY = "buy"
    SELL = "sell"


@unique
class PriceTypeEnum(Enum):
    """价格类型"""
    LIMIT = "limit"
    MARKET = "market"


@unique
class TradeTypeEnum(Enum):
    """交易类型"""
    T0 = "T0"
    T1 = "T1"


@unique
class OrderStatusEnum(Enum):
    """订单状态"""
    WAITING = "等待中"
    PART_FINISHED = "部分成交"
    ALL_FINISHED = "全部成交"
    CANCELED = "已取消"
    REJECTED = "已拒单"
