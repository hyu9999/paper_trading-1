import aioredis
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


async def connect_to_redis() -> None:
    logger.info("连接Redis中...")
    state.user_redis_pool = await aioredis.create_redis_pool(
        f"redis://{settings.redis.host}:{settings.redis.port}/{settings.redis.user_db}?encoding=utf-8"
    )
    logger.info("Redis已连接.")


async def close_redis_connection() -> None:
    logger.info("关闭Redis连接池中...")
    try:
        state.user_redis_pool.close()
    except aioredis.errors.ConnectionForcedCloseError:
        pass
    await state.user_redis_pool.wait_closed()
    logger.info("Redis连接池已关闭.")
