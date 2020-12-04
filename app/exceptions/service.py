class ServiceError(Exception):
    """服务异常基类."""


class NotEnoughAvailableAddr(ServiceError):
    """可用的行情地址不足时触发."""


class InsufficientFunds(ServiceError):
    """资金不足时触发."""

    msg = "账户资金不足."


class InvalidExchange(ServiceError):
    """订单指定的交易所不在于市场引擎规定的交易所列表中时触发."""


class NoPositionsAvailable(ServiceError):
    """用户未持有订单指定的股票时触发."""

    msg = "账户无可用持仓."


class NotEnoughAvailablePositions(ServiceError):
    """用户持仓股票可用数量不足时触发."""

    msg = "账户可用持仓不足."


class GetQuotesFailed(ServiceError):
    """获取行情失败时触发."""
