import asyncio
from datetime import date, datetime

from app import settings, state
from app.db.cache.user import UserCache
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def sync_user_assets_task():
    """同步用户资产相关数据."""
    user_cache = UserCache(state.user_redis_pool)
    user_engine = state.engine.user_engine
    start_time = datetime.combine(date.today(), market_class.OPEN_MARKET_TIME)
    end_time = datetime.combine(date.today(), market_class.CLOSE_MARKET_TIME)
    users = await user_cache.get_all_user()
    while start_time < datetime.now() < end_time:
        await asyncio.gather(
            *[user_engine.liquidate_user_position(user.id) for user in users]
        )
        await asyncio.gather(
            *[user_engine.liquidate_user_profit(user.id) for user in users]
        )
