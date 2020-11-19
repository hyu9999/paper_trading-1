from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query
from starlette import status as http_status

from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.statement import StatementRepository
from app.models.domain.users import UserInDB
from app.models.domain.statement import StatementInDB

router = APIRouter()


@router.get(
    "/",
    status_code=http_status.HTTP_200_OK,
    name="orders:get-statement-list",
    response_model=List[StatementInDB]
)
async def get_statement_list(
    statement_repo: StatementRepository = Depends(get_repository(StatementRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
    start_date: date = Query(None, description="开始时间"),
    end_date: date = Query(None, description="结束时间"),
):
    return await statement_repo.get_statement_list(user_id=user.id, start_date=start_date, end_date=end_date)
