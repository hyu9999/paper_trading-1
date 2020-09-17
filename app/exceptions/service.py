class ServiceError(Exception):
    """服务异常基类
    """


class NotEnoughAvailableAddr(ServiceError):
    """可用的行情地址不足时触发
    """
