from typing import Type, Callable

from app import settings, state
from app.db.utils import codec_option
from app.db.cache.user import UserCache
from app.db.repositories.base import BaseRepository


def get_repository(repo_type: Type[BaseRepository]) -> Callable:
    def _get_repo(
    ) -> BaseRepository:
        return repo_type(state.db_client.get_database(settings.db.name, codec_options=codec_option))
    return _get_repo


def get_user_cache():
    return UserCache(state.user_redis_pool)
