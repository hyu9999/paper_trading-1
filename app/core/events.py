from hq2redis import HQ2Redis
from loguru import logger

from app import settings, state
from app.core.logging import init_logger
from app.db.events import (
    close_db_connection,
    close_redis_connection,
    connect_to_db,
    connect_to_redis,
)
from app.schedulers import load_jobs_with_lock, stop_jobs
from app.services.events import close_engine, start_engine


async def connect_to_quotes_api():
    quotes_api = HQ2Redis(
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        redis_db=settings.redis.hq_db,
        jqdata_password=settings.jqdata_password,
        jqdata_user=settings.jqdata_user,
    )
    await quotes_api.startup()
    state.quotes_api = quotes_api


async def close_quotes_api_conn():
    await state.quotes_api.shutdown()


async def start_app() -> None:
    await init_logger()
    await connect_to_db()
    await connect_to_redis()
    await connect_to_quotes_api()
    await start_engine()
    await load_jobs_with_lock()


@logger.catch
async def stop_app() -> None:
    await stop_jobs()
    await close_engine()
    await close_redis_connection()
    await close_db_connection()
    await close_quotes_api_conn()
