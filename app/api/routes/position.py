from typing import List

from fastapi import APIRouter, Depends
from starlette import status

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_position_cache
from app.db.cache.position import PositionCache
from app.models.domain.users import UserInDB
from app.models.schemas.position import PositionInCache

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="position:get-position-list",
    response_model=List[PositionInCache],
)
async def get_position_list(
    user: UserInDB = Depends(get_current_user_authorizer()),
    position_cache: PositionCache = Depends(get_position_cache),
) -> List[PositionInCache]:
    return await position_cache.get_position_by_user_id(user.id)
