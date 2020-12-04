from bson.errors import InvalidId
from fastapi import APIRouter, Depends
from starlette import status

from app.api.dependencies.database import get_repository, get_user_cache
from app.core import jwt
from app.db.cache.user import UserCache
from app.db.repositories.user import UserRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.http import InvalidUserID
from app.models.schemas.users import (
    UserInCache,
    UserInCreate,
    UserInLogin,
    UserInResponse,
)

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInResponse,
    name="auth:register",
)
async def register(
    user_in_create: UserInCreate,
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    user_cache: UserCache = Depends(get_user_cache),
):
    user = await user_repo.create_user(user_in_create)
    token = jwt.create_access_token_for_user(user_id=user.id)
    await user_cache.set_user(UserInCache(**user.dict()))
    return UserInResponse(**user.dict(), token=token)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserInResponse,
    name="auth:login",
)
async def login(
    user_login: UserInLogin,
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
) -> UserInResponse:
    try:
        user = await user_repo.get_user_by_id(user_id=user_login.id)
    except (InvalidId, EntityDoesNotExist):
        raise InvalidUserID
    else:
        token = jwt.create_access_token_for_user(user_id=user_login.id)
        return UserInResponse(**user.dict(), token=token)
