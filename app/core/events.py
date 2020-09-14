from typing import Callable

from loguru import logger
from fastapi import FastAPI

from app.core.logging import init_logger


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
       await init_logger()
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    @logger.catch
    async def stop_app() -> None:
        pass
    return stop_app
