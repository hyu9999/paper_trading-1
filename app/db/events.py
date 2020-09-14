from fastapi import FastAPI
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings


async def connect_to_db(app: FastAPI) -> None:
    logger.info(f"连接数据库中...")
    app.state.db = AsyncIOMotorClient(settings.db.url, maxPoolSize=settings.db.max_connections,
                                      minPoolSize=settings.db.min_connections)
    logger.info("连接数据库成功.")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("关闭数据库连接...")
    app.state.db.close()
    logger.info("数据库连接已关闭.")
