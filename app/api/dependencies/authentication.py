from typing import Callable, Optional

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from starlette import requests
from starlette.exceptions import HTTPException

from app import settings
from app.api.dependencies.database import get_repository
from app.core import jwt
from app.models.domain.users import UserInDB
from app.db.repositories.user import UserRepository
from app.exceptions.http import InvalidAuthTokenPrefix, AuthHeaderNotFound, InvalidAuthToken, WrongTokenFormat

HEADER_KEY = "Authorization"


class RWAPIKeyHeader(APIKeyHeader):
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
    try:
        user_id = jwt.get_user_id_from_token(token)
    except ValueError:
        raise InvalidAuthToken
    return await user_repo.get_user_by_id(user_id=user_id)


async def _get_current_user_optional(
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    token: Optional[str] = Depends(_get_authorization_token),
) -> Optional[UserInDB]:
    if token:
        return await _get_current_user(user_repo, token)
    return None




