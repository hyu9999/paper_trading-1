from starlette import status
from fastapi import APIRouter, Depends, Path

from app.api.dependencies.database import get_repository, get_user_cache
from app.db.cache.user import UserCache
from app.db.repositories.user import UserRepository
from app.db.repositories.order import OrderRepository
from app.exceptions.http import InvalidUserID
from app.exceptions.db import EntityDoesNotExist
from app.models.types import PyObjectId
from app.models.schemas.users import ListOfUserInResponse, UserInResponse, UserInCache

router = APIRouter()


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserInCache,
    name="users:get-user"
)
async def get_user(
    user_id: PyObjectId = Path(..., description="用户ID"),
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    user_cache: UserCache = Depends(get_user_cache),
) -> UserInCache:
    try:
        user = await user_cache.get_user_by_id(user_id)
    except EntityDoesNotExist:
        raise InvalidUserID
    return user


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ListOfUserInResponse,
    name="users:list-users"
)
async def list_users(
    user_repo: UserRepository = Depends(get_repository(UserRepository))
) -> ListOfUserInResponse:
    users = await user_repo.get_user_list()
    return ListOfUserInResponse(users=users, count=len(users))
