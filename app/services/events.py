from fastapi import FastAPI
from loguru import logger

from app.services.engines.trade_engine import TradeEngine


async def start_engine(app: FastAPI) -> None:
    logger.info("开启模拟交易主引擎中...")
    app.state.engine = TradeEngine(app.state.db)
    logger.info("模拟交易主引擎已开启.")


async def close_engine(app: FastAPI) -> None:
    logger.info("关闭模拟交易主引擎中...")
    logger.info("模拟交易主引擎已关闭.")
