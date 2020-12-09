from typing import List, Optional

from fastapi.encoders import jsonable_encoder

from app import settings
from app.db.cache.base import BaseCache
from app.exceptions.db import EntityDoesNotExist
from app.models.enums import ExchangeEnum
from app.models.schemas.position import PositionInCache
from app.models.types import PyObjectId


class PositionCache(BaseCache):
    DB = settings.redis.position_db
    POSITION_KEY = "position_{user}.{symbol}.{exchange}"  # REDIS KEY
    POSITION_KEY_PREFIX = "position_"

    async def set_position(
        self,
        position: PositionInCache,
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ) -> None:
        await self._cache.hmset_dict(
            self.POSITION_KEY.format(
                user=position.user,
                symbol=position.symbol,
                exchange=position.exchange,
            ),
            jsonable_encoder(position, include=include, exclude=exclude),
        )

    async def update_position(
        self,
        position: PositionInCache,
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ):
        key = self.POSITION_KEY.format(
            user=position.user,
            symbol=position.symbol,
            exchange=position.exchange,
        )
        if await self._cache.exists(key):
            await self._cache.hmset_dict(
                key, jsonable_encoder(position, include=include, exclude=exclude)
            )

    async def update_position_many(
        self,
        position_list: List[PositionInCache],
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ):
        pipeline = self._cache.pipeline()
        for position in position_list:
            key = self.POSITION_KEY.format(
                user=position.user,
                symbol=position.symbol,
                exchange=position.exchange,
            )
            if await self._cache.exists(key):
                pipeline.hmset_dict(
                    key, jsonable_encoder(position, include=include, exclude=exclude)
                )
        await pipeline.execute()

    async def set_position_many(
        self,
        position_list: List[PositionInCache],
        include: Optional[set] = None,
        exclude: Optional[set] = None,
    ) -> None:
        pipeline = self._cache.pipeline()
        for position in position_list:
            pipeline.hmset_dict(
                self.POSITION_KEY.format(
                    user=position.user,
                    symbol=position.symbol,
                    exchange=position.exchange,
                ),
                jsonable_encoder(position, include=include, exclude=exclude),
            )
        await pipeline.execute()

    async def get_position_by_user_id(
        self, user_id: PyObjectId
    ) -> List[PositionInCache]:
        pipeline = self._cache.pipeline()
        for key in await self.get_keys(f"{self.POSITION_KEY_PREFIX}{user_id}*"):
            pipeline.hgetall(key)
        return [PositionInCache(**position) for position in await pipeline.execute()]

    async def get_position(
        self, user_id: PyObjectId, symbol: str, exchange: ExchangeEnum
    ) -> PositionInCache:
        position_in_cache = await self._cache.hgetall(
            self.POSITION_KEY.format(user=user_id, symbol=symbol, exchange=exchange)
        )
        if not position_in_cache:
            raise EntityDoesNotExist
        return PositionInCache(**position_in_cache)

    async def delete_position(self, position: PositionInCache) -> None:
        await self._cache.delete(
            self.POSITION_KEY.format(
                user=position.user, symbol=position.symbol, exchange=position.exchange
            )
        )

    async def delete_position_by_user(self, user_id: PyObjectId) -> None:
        pipeline = self._cache.pipeline()
        for key in await self.get_keys(f"{self.POSITION_KEY_PREFIX}{user_id}*"):
            pipeline.delete(key)
        await pipeline.execute()
