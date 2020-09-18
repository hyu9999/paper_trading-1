from fastapi import FastAPI
from loguru import logger
from threading import Thread

from app.services.engines.trade_engine import TradeEngine
from app.services.engines.event_engine import EventEngine


foo = None


class Foo:
    def __init__(self):
        self.thread = Thread(target=self.run)
        self.thread1 = Thread(target=self.run)

    def start(self):
        self.thread.start()
        self.thread1.start()

    def stop(self):
        print(1111)
        self.thread.join()
        self.thread1.join()

    def run(self):
        pass


async def start_engine(app: FastAPI) -> None:
    logger.info("开启模拟交易主引擎中...")
    app.state.engine = TradeEngine()
    await app.state.engine.start()
    logger.info("模拟交易主引擎已开启.")


async def close_engine(app: FastAPI) -> None:
    logger.info("关闭模拟交易主引擎中...")
    await app.state.engine.stop()
    logger.info("模拟交易主引擎已关闭.")
