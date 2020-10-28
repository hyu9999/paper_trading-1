from loguru import logger

from app import settings, state
from app.db.utils import codec_option
from app.services.engines.main_engine import MainEngine


async def start_engine() -> None:
    logger.info("开启模拟交易主引擎中...")
    state.engine = MainEngine(
        state.db_client.get_database(settings.db.name, codec_options=codec_option),
        state.quotes_api
    )
    await state.engine.startup()
    logger.info("模拟交易主引擎已开启.")


async def close_engine() -> None:
    logger.info("关闭模拟交易主引擎中...")
    await state.engine.shutdown()
    logger.info("模拟交易主引擎已关闭.")
