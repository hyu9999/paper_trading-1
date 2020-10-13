from fastapi import FastAPI
from loguru import logger

from app import settings
from app.db.utils import codec_option
from app.services.engines.main_engine import MainEngine


async def start_engine(app: FastAPI) -> None:
    logger.info("开启模拟交易主引擎中...")
    app.state.engine = MainEngine(
        app.state.db_client.get_database(settings.db.name, codec_options=codec_option)
    )
    await app.state.engine.startup()
    logger.info("模拟交易主引擎已开启.")


async def close_engine(app: FastAPI) -> None:
    logger.info("关闭模拟交易主引擎中...")
    await app.state.engine.shutdown()
    logger.info("模拟交易主引擎已关闭.")
