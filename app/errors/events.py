from fastapi import FastAPI
from loguru import logger

from app.errors import http


async def register_exceptions(app: FastAPI):
    """注册http异常"""
    app.add_exception_handler(http.InvalidLoginInput, http.InvalidLoginInput.handler)
    logger.info("注册自定义HTTP异常类别完成.")
