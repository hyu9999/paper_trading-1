from fastapi import FastAPI
from loguru import logger
# from threading import Thread
import multiprocessing as mp

from app.services.engines.engine import Engine
from app.services.engines.event_engine import EventEngine


class Foo:
    def __init__(self):
        self.event_engine = EventEngine()
        self.event_engine.start()
        self.thread = mp.Process(target=self.run)

    def start(self):
        self.thread.start()

    def close(self):
        self.thread.join()

    def run(self):
        pass


async def start_engine(app: FastAPI) -> None:
    logger.info("开启模拟交易主引擎中...")
    app.state.engine = Engine()
    app.state.engine.start()
    # app.state.engine = Foo()
    # app.state.engine.start()
    logger.info("模拟交易主引擎已开启.")


async def close_engine(app: FastAPI) -> None:
    logger.info("关闭模拟交易主引擎中...")
    app.state.engine.close()
    logger.info("模拟交易主引擎已关闭.")
