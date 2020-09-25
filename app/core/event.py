import signal
import asyncio
from typing import Callable

from loguru import logger
from fastapi import FastAPI

from app import settings
from app.core.logging import init_logger
from app.db.events import connect_to_db, close_db_connection, connect_to_redis, close_redis_connection
from app.exceptions.events import register_exceptions
from app.services.events import start_engine, close_engine

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


async def install_signal_handlers(app: FastAPI) -> None:
    if settings.env_for_dynaconf == "development":
        loop = asyncio.get_event_loop()
        for sig in HANDLED_SIGNALS:
            loop.add_signal_handler(sig, handle_exit, app)


def handle_exit(app: FastAPI):
    pass
    # print(1, app.state.engine.market_engine.quotes_api.api.ippool)
    # print(2, app.state.engine.market_engine.quotes_api.api.ippool.worker_thread)
    # app.state.engine.market_engine.quotes_api.close()
    # app.state.engine.market_engine.quotes_api.api.ippool.worker_thread.join()
    # print(3, app.state.engine.market_engine)


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await init_logger()
        await connect_to_db(app)
        await connect_to_redis(app)
        await register_exceptions(app)
        await start_engine(app)
        # await install_signal_handlers(app)
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)
        await close_redis_connection(app)
        await close_engine(app)
    return stop_app
