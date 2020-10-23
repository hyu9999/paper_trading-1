import asyncio
from decimal import Decimal

from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.utils import codec_option
from app.db.repositories.user import UserRepository
from app.db.repositories.position import PositionRepository
from app.models.schemas.users import UserInUpdate
from app.models.types import PyDecimal
from app.models.schemas.position import PositionInUpdate
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from app.services.quotes.constant import quotes_mapping

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def sync_user_assets():
    quotes_api = quotes_mapping[settings.quotes_api]()
    db_client = AsyncIOMotorClient(settings.db.url, maxPoolSize=settings.db.max_connections,
                                   minPoolSize=settings.db.min_connections)
    db_database = db_client.get_database(settings.db.name, codec_options=codec_option)
    user_repo = UserRepository(db_database)
    position_repo = PositionRepository(db_database)
    users = await user_repo.get_users_list()
    while market_class.is_trading_time():
        for user in users:
            user_position = await position_repo.get_positions_by_user_id(user_id=user.id)
            if not user_position:
                continue
            position_mapping = {position.stock_code: position for position in user_position}
            quotes_list = await quotes_api.get_current_tick(position_mapping.keys())
            for quotes in quotes_list:
                position = position_mapping[quotes.stock_code]
                current_price = quotes.ask1_p
                position_in_update = PositionInUpdate(**position.dict())
                position_in_update.current_price = current_price
                profit = (current_price.to_decimal() - position.cost.to_decimal()) * Decimal(position.volume) \
                    + position.profit.to_decimal()
                position_in_update.profit = PyDecimal(profit)
                await position_repo.update_position(position_in_update)
                # 用户资产
                securities = sum([position.current_price.to_decimal() * Decimal(position.volume)
                                  for position in user_position])
                assets = user.cash.to_decimal() + securities
                user_in_update = UserInUpdate(**user.dict())
                if securities != Decimal(0):
                    user_in_update.securities = PyDecimal(securities)
                user_in_update.assets = PyDecimal(assets)
                await user_repo.update_user(user_in_update)
        await asyncio.sleep(3)
