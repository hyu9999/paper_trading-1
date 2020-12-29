from fastapi import APIRouter, Body, Depends, Path
from starlette import status

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import (
    get_position_cache,
    get_repository,
    get_user_cache,
)
from app.api.dependencies.state import get_engine
from app.db.cache.position import PositionCache
from app.db.cache.user import UserCache
from app.db.repositories.user import UserRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.http import InvalidUserID, NotTradingTime
from app.models.domain.users import UserInDB
from app.models.schemas.http import HttpMessage
from app.models.schemas.users import ListOfUserInResponse, UserInCache, UserInUpdateCash
from app.models.types import PyDecimal, PyObjectId
from app.services.engines.main_engine import MainEngine

router = APIRouter()


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserInCache,
    name="users:get-user",
)
async def get_user(
    user_id: PyObjectId = Path(..., description="用户ID"),
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
    name="users:list-users",
)
async def list_users(
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
) -> ListOfUserInResponse:
    users = await user_repo.get_user_list()
    return ListOfUserInResponse(users=users, count=len(users))


@router.put("/terminate", status_code=status.HTTP_200_OK, name="users:terminate")
async def terminate(
    user: UserInDB = Depends(get_current_user_authorizer()),
    user_repo: UserRepository = Depends(get_repository(UserRepository)),
    user_cache: UserCache = Depends(get_user_cache),
    position_cache: PositionCache = Depends(get_position_cache),
):
    """停用账户."""
    await user_repo.terminate_user(user.id)
    await user_cache.delete_key(str(user.id))
    await position_cache.delete_position_by_user(user.id)
    return HttpMessage(text="停用账户成功.")


@router.put(
    "/cash",
    status_code=status.HTTP_200_OK,
    name="users:cash",
    response_model=UserInCache,
)
async def update_cash(
    user: UserInDB = Depends(get_current_user_authorizer()),
    user_in_update: UserInUpdateCash = Body(...),
    engine: MainEngine = Depends(get_engine),
    user_cache: UserCache = Depends(get_user_cache),
) -> UserInCache:
    """修改用户可用现金(出金入金)."""
    if not engine.market_engine.is_trading_time():
        raise NotTradingTime
    try:
        user_in_cache = await user_cache.get_user_by_id(user.id)
    except EntityDoesNotExist:
        user_in_cache = UserInCache(**user.dict())
    else:
        await user_cache.set_user(user_in_cache)
    diff = user_in_update.cash.to_decimal() - user_in_cache.available_cash.to_decimal()
    user_in_cache.available_cash = PyDecimal(
        user_in_cache.available_cash.to_decimal() + diff
    )
    user_in_cache.cash = PyDecimal(user_in_cache.cash.to_decimal() + diff)
    user_in_cache.assets = PyDecimal(user_in_cache.assets.to_decimal() + diff)
    await user_cache.update_user(
        user_in_cache, include={"cash", "available_cash", "assets"}
    )
    return user_in_cache
