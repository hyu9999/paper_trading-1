import asyncio
from datetime import datetime, date

from app import settings, state
from app.db.utils import codec_option
from app.db.repositories.user import UserRepository
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def sync_user_assets():
    db_database = state.db_client.get_database(settings.db.name, codec_options=codec_option)
    user_repo = UserRepository(db_database)
    users = await user_repo.get_users_list()
    user_engine = state.engine.user_engine
    start_time = datetime.combine(date.today(), market_class.OPEN_MARKET_TIME)
    end_time = datetime.combine(date.today(), market_class.CLOSE_MARKET_TIME)
    while start_time < datetime.now() < end_time:
        for user in users:
            await user_engine.liquidate_user_position(user)
            await user_engine.liquidate_user_profit(user)
        await asyncio.sleep(3)
