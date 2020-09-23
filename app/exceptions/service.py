class ServiceError(Exception):
    """服务异常基类."""


class NotEnoughAvailableAddr(ServiceError):
    """可用的行情地址不足时触发."""


class InsufficientFunds(ServiceError):
    """资金不足时触发."""


class InvalidExchange(ServiceError):
    """订单指定的交易所不在于市场引擎规定的交易所列表中时触发"""
