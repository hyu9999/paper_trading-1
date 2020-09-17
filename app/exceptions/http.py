from starlette import status

from starlette.requests import Request
from starlette.responses import JSONResponse


class _HTTPException(Exception):
    detail = "HTTP异常"
    code = 10000
    status_code = status.HTTP_400_BAD_REQUEST

    @classmethod
    async def handler(cls, request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=cls.status_code, content={"code": cls.code, "detail": cls.detail})


class InvalidUserID(_HTTPException):
    code = 10001
    detail = "用户ID无效"


class InvalidAuthTokenPrefix(_HTTPException):
    code = 10002
    detail = "无效的Token前缀"


class AuthHeaderNotFound(_HTTPException):
    code = 10003
    detail = "未找到认证请求头"


class InvalidAuthToken(_HTTPException):
    code = 10004
    detail = "该Token无效"


class WrongTokenFormat(_HTTPException):
    code = 10004
    detail = "错误的Token格式"
