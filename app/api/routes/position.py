from typing import List

from starlette import status
from fastapi import APIRouter, Depends

from app.api.dependencies.state import get_engine
from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.models.domain.users import UserInDB
from app.models.schemas.position import PositionInResponse
from app.db.repositories.position import PositionRepository
from app.services.engines.main_engine import MainEngine

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="position:get-position-list",
    response_model=List[PositionInResponse]
)
async def get_position_list(
    position_repo: PositionRepository = Depends(get_repository(PositionRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
    engine: MainEngine = Depends(get_engine),
):
    await engine.user_engine.liquidate_user_position(user)
    position_list = await position_repo.get_positions_by_user_id(user_id=user.id)
    return [PositionInResponse(**dict(position)) for position in position_list]
