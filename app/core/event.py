from typing import Callable

from loguru import logger
from fastapi import FastAPI
from hq2redis import HQ2Redis

from app import settings, state
from app.core.logging import init_logger
from app.db.events import connect_to_db, close_db_connection
from app.exceptions.events import register_exceptions
from app.schedulers import load_jobs_with_lock
from app.services.events import start_engine, close_engine


async def connect_to_quotes_api():
    quotes_api = HQ2Redis(
        redis_host=settings.redis.host,
        redis_port=settings.redis.port,
        redis_db=settings.redis.hq_db,
        jq_data_password=settings.jqdata_password,
        jq_data_user=settings.jqdata_user,
    )
    await quotes_api.startup()
    state.quotes_api = quotes_api


async def close_quotes_api_conn():
    await state.quotes_api.shutdown()


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        await init_logger()
        await connect_to_db()
        await register_exceptions(app)
        await connect_to_quotes_api()
        await start_engine()
        await load_jobs_with_lock()
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection()
        await close_engine()
        await close_quotes_api_conn()
    return stop_app
