from starlette import status

from starlette.requests import Request
from starlette.responses import JSONResponse


class _HTTPException(Exception):
    detail = "HTTP异常"
    code = 10000
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, *args, **kwargs):
        self.status_code = kwargs.get("status_code")
        self.detail = kwargs.get("detail")

    @classmethod
    async def handler(cls, request: Request, exc: Exception) -> JSONResponse:
        print(exc)
        return JSONResponse(status_code=exc.__dict__.get("status_code") or cls.status_code,
                            content={"code": cls.code, "detail": exc.__dict__.get("detail") or cls.detail})


class InvalidUserID(_HTTPException):
    code = 10001
    detail = "该用户ID无效"


class InvalidAuthTokenPrefix(_HTTPException):
    code = 10002
    detail = "无效的Token前缀"


class AuthHeaderNotFound(_HTTPException):
    code = 10003
    detail = "未找到认证请求头"


class InvalidAuthToken(_HTTPException):
    code = 10004
    detail = "无效的Token"


class WrongTokenFormat(_HTTPException):
    code = 10005
    detail = "错误的Token格式"


class InvalidAuthMode(_HTTPException):
    code = 10006
    detail = "无效的认证模式"


class InsufficientAccountFunds(_HTTPException):
    code = 10021
    detail = "账户资金不足"


class InvalidOrderExchange(_HTTPException):
    code = 10022
    detail = "订单指定的交易所无效"


class OrderNotFound(_HTTPException):
    code = 10023
    detail = "未找到该订单"


class NotTradingTime(_HTTPException):
    code = 10024
    detail = "非交易时段，无法进行交易"


class CancelOrderFailed(_HTTPException):
    code = 10024
    detail = "提交撤单请求失败"
