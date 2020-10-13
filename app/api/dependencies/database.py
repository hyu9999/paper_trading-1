from typing import Type, Callable

from fastapi import Depends
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.db.utils import codec_option
from app.db.repositories.base import BaseRepository


def _get_db_client(request: Request) -> AsyncIOMotorClient:
    return request.app.state.db_client


def get_repository(repo_type: Type[BaseRepository]) -> Callable:
    def _get_repo(
        client: AsyncIOMotorClient = Depends(_get_db_client),
    ) -> BaseRepository:
        return repo_type(client.get_database(settings.db.name, codec_options=codec_option))
    return _get_repo
