import random
import asyncio
from time import perf_counter
from datetime import datetime, date

from app.db.cache.user import UserCache
from app.models.types import PyObjectId

from app import settings, state
from app.db.utils import codec_option
from app.db.repositories.user import UserRepository
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def sync_user_assets_task():
    """同步用户资产相关数据."""
    db_database = state.db_client.get_database(settings.db.name, codec_options=codec_option)
    user_repo = UserRepository(db_database)
    user_cache = UserCache(state.user_redis_pool)
    user_engine = state.engine.user_engine
    start_time = datetime.combine(date.today(), market_class.OPEN_MARKET_TIME)
    end_time = datetime.combine(date.today(), market_class.CLOSE_MARKET_TIME)
    # while start_time < datetime.now() < end_time:
    # while True:
    #     pass
        # users = await user_cache.get_all_user()
        # await asyncio.gather(*[user_engine.liquidate_user_position(user) for user in users])
        # await asyncio.gather(*[user_engine.liquidate_user_profit(user) for user in users])
