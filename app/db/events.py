import aioredis
from fastapi import FastAPI
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings


async def connect_to_db(app: FastAPI) -> None:
    logger.info("连接数据库中...")
    app.state.db = AsyncIOMotorClient(settings.db.url, maxPoolSize=settings.db.max_connections,
                                      minPoolSize=settings.db.min_connections)
    logger.info("数据库已连接.")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("关闭数据库连接中...")
    app.state.db.close()
    logger.info("数据库连接已关闭.")


async def connect_to_redis(app: FastAPI) -> None:
    logger.info("连接Redis中...")
    app.state.entrust_db = aioredis.create_redis_pool(
        settings.redis.entrust_url, encoding=settings.redis.encoding
    )
    logger.info("Redis已连接.")


async def close_redis_connection(app: FastAPI) -> None:
    logger.info("关闭Redis连接中...")
    app.state.entrust_db.close()
    await app.state.entrust_db.wait_closed()
    logger.info("Redis连接已关闭.")