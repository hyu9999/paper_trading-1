from starlette.requests import Request
from starlette.responses import JSONResponse


class BaseError(Exception):
    code = 10000
    message = "标准错误"

    @classmethod
    def get_error_msg(cls, exc: Exception):
        return {"code": cls.code, "message": str(exc)}

    @classmethod
    async def handler(cls, request: Request, exc: Exception):
        return JSONResponse(status_code=400, content=cls.get_error_msg(exc))


class InvalidLoginInput(BaseError):
    code = 10001
    message = "登陆参数错误"
