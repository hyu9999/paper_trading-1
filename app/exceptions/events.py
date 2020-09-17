from fastapi import FastAPI
from loguru import logger

from app.exceptions import http


async def register_exceptions(app: FastAPI):
    """注册自定义HTTP异常"""
    app.add_exception_handler(http.InvalidUserID, http.InvalidUserID.handler)
    app.add_exception_handler(http.InvalidAuthTokenPrefix, http.InvalidAuthTokenPrefix.handler)
    app.add_exception_handler(http.AuthHeaderNotFound, http.AuthHeaderNotFound.handler)
    app.add_exception_handler(http.InvalidAuthToken, http.InvalidAuthToken.handler)
    app.add_exception_handler(http.WrongTokenFormat, http.WrongTokenFormat.handler)
    logger.info("注册自定义HTTP异常类别完成.")