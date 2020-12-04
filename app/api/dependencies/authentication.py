from typing import Callable, Optional

from bson.errors import InvalidId
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from starlette import requests
from starlette.exceptions import HTTPException

from app import settings
from app.api.dependencies.database import get_repository
from app.core import jwt
from app.db.repositories.user import UserRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.http import (
    AuthHeaderNotFound,
    InvalidAuthMode,
    InvalidAuthToken,
    InvalidAuthTokenPrefix,
    InvalidUserID,
    WrongTokenFormat,
)
from app.models.domain.users import UserInDB
from app.models.types import PyObjectId

HEADER_KEY = "Authorization"


class RWAPIKeyHeader(APIKeyHeader):
    """获取请求头的鉴权字段."""

    async def __call__(
        self,
        request: requests.Request,
    ) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            raise AuthHeaderNotFound


def _get_authorization_token(
    api_key: str = Security(RWAPIKeyHeader(name=HEADER_KEY)),
) -> str:
    try:
        token_prefix, token = api_key.split(" ")
    except ValueError:
        raise WrongTokenFormat
    if token_prefix != settings.token_prefix:
        raise InvalidAuthTokenPrefix
    return token


def get_current_user_authorizer(*, required: bool = True) -> Callable:
    return _get_current_user if required else _get_current_user_optional


async def _get_current_user(
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    token: str = Depends(_get_authorization_token),
) -> UserInDB:
    if settings.auth_mode == "JWT":
        try:
            user_id = jwt.get_user_id_from_token(token)
        except ValueError:
            raise InvalidAuthToken
    elif settings.auth_mode == "UID":
        user_id = token
    else:
        raise InvalidAuthMode
    try:
        user_object_id = PyObjectId(user_id)
    except InvalidId:
        raise InvalidAuthToken
    try:
        return await user_repo.get_user_by_id(user_id=user_object_id)
    except EntityDoesNotExist:
        raise InvalidUserID


async def _get_current_user_optional(
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    token: Optional[str] = Depends(_get_authorization_token),
) -> Optional[UserInDB]:
    if token:
        return await _get_current_user(user_repo, token)
    return None
