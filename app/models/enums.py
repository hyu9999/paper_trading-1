from enum import Enum, unique


@unique
class ExchangeEnum(str, Enum):
    """股票市场."""

    SH = "SH"
    SZ = "SZ"


@unique
class JWTSubjectEnum(str, Enum):
    """JWT主题."""

    ACCESS = "access"


@unique
class OrderTypeEnum(str, Enum):
    """委托订单类型."""

    BUY = "buy"
    SELL = "sell"
    CANCEL = "cancel"


@unique
class TradeCategoryEnum(str, Enum):
    """交易类别."""

    BUY = "buy"  # 证券买入
    SELL = "sell"  # 证券卖出


@unique
class PriceTypeEnum(str, Enum):
    """价格类型."""

    LIMIT = "limit"
    MARKET = "market"


@unique
class TradeTypeEnum(str, Enum):
    """交易类型."""

    T0 = "T0"
    T1 = "T1"


@unique
class OrderStatusEnum(str, Enum):
    """订单状态."""

    SUBMITTING = "提交中"
    NOT_DONE = "未成交"
    PART_FINISHED = "部分成交"
    ALL_FINISHED = "全部成交"
    CANCELED = "已撤销"
    REJECTED = "已拒单"


@unique
class EntrustOrdersModeEnum(str, Enum):
    """委托单模式"""

    TIME_PRIORITY = "时间优先"
    PRICE_PRIORITY = "价格优先"


@unique
class UserStatusEnum(str, Enum):
    """用户状态."""

    ACTIVATED = "已启用"
    TERMINATED = "已停用"
