from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings, state


async def connect_to_db() -> None:
    logger.info("连接数据库中...")
    state.db_client = AsyncIOMotorClient(settings.db.url, maxPoolSize=settings.db.max_connections,
                                         minPoolSize=settings.db.min_connections)
    logger.info("数据库已连接.")


async def close_db_connection() -> None:
    logger.info("关闭数据库连接中...")
    state.db_client.close()
    logger.info("数据库连接已关闭.")
