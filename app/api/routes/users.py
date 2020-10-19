from starlette import status
from fastapi import APIRouter, Depends, Path

from app.api.dependencies.state import get_engine
from app.api.dependencies.database import get_repository
from app.db.repositories.user import UserRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.http import InvalidUserID
from app.models.types import PyObjectId
from app.models.schemas.users import ListOfUserInResponse, UserInResponse
from app.services.engines.main_engine import MainEngine

router = APIRouter()


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserInResponse,
    name="users:get-user"
)
async def get_user(
    user_id: PyObjectId = Path(..., description="用户ID"),
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    engine: MainEngine = Depends(get_engine),
) -> UserInResponse:
    try:
        user = await user_repo.get_user_by_id(user_id)
    except EntityDoesNotExist:
        raise InvalidUserID
    await engine.user_engine.liquidate_user_position(user)
    user_in_update = await engine.user_engine.liquidate_user_profit(user)
    user.cash = user_in_update.cash
    user.securities = user_in_update.securities
    user.assets = user_in_update.assets
    return UserInResponse(**user.dict())


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ListOfUserInResponse,
    name="users:list-users"
)
async def list_users(
    user_repo: UserRepository = Depends(get_repository(UserRepository))
) -> ListOfUserInResponse:
    users = await user_repo.get_users_list()
    return ListOfUserInResponse(users=users, count=len(users))
