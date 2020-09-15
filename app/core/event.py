from typing import Callable

from loguru import logger
from fastapi import FastAPI

from app.core.logging import init_logger
from app.db.events import connect_to_db, close_db_connection, connect_to_redis, close_redis_connection
from app.errors.events import register_exceptions


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await init_logger()
        await connect_to_db(app)
        await connect_to_redis(app)
        await register_exceptions(app)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)
        await close_redis_connection(app)
    return stop_app
