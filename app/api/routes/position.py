from typing import List

from fastapi import APIRouter, Body, Depends
from starlette import status

from app import state
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_position_cache, get_repository
from app.db.cache.position import PositionCache
from app.db.repositories.position import PositionRepository
from app.db.repositories.statement import StatementRepository
from app.models.base import get_utc_now
from app.models.domain.statement import Costs, StatementInDB
from app.models.domain.users import UserInDB
from app.models.schemas.http import HttpMessage
from app.models.schemas.position import (
    PositionInCache,
    PositionInCreate,
    PositionInManualCreate,
)
from app.models.types import PyDecimal

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


@router.post(
    "/manual_import",
    status_code=status.HTTP_201_CREATED,
    name="position:manual_import_position",
)
async def manual_import_position(
    user: UserInDB = Depends(get_current_user_authorizer()),
    position_in_create: PositionInManualCreate = Body(...),
    statement_repo: StatementRepository = Depends(get_repository(StatementRepository)),
    position_repo: PositionRepository = Depends(get_repository(PositionRepository)),
    position_cache: PositionCache = Depends(get_position_cache),
):
    # 创建交割单
    costs = Costs(total=PyDecimal("0"), commission=PyDecimal("0"), tax=PyDecimal("0"))
    statement_in_db = StatementInDB(
        symbol=position_in_create.symbol,
        exchange=position_in_create.exchange,
        entrust_id=None,
        user=user.id,
        trade_category="buy",
        volume=position_in_create.volume,
        sold_price=position_in_create.cost,
        amount=PyDecimal(
            position_in_create.cost.to_decimal() * position_in_create.volume
        ),
        costs=costs,
        deal_time=get_utc_now(),
    )
    await statement_repo.create_statement(statement_in_db)
    quotes = await state.quotes_api.get_stock_ticks(position_in_create.stock_code)
    # 创建持仓
    position_in_create = PositionInCreate(
        symbol=position_in_create.symbol,
        exchange=position_in_create.exchange,
        user=user.id,
        volume=position_in_create.volume,
        available_volume=position_in_create.volume,
        cost=position_in_create.cost,
        current_price=PyDecimal(quotes.current),
        profit=PyDecimal(
            (quotes.current - position_in_create.cost.to_decimal())
            * position_in_create.volume
        ),
        first_buy_date=get_utc_now(),
    )
    await position_repo.create_position(**position_in_create.dict())
    position_in_cache = PositionInCache(**position_in_create.dict())
    await position_cache.set_position(position_in_cache)
    return HttpMessage(text="手动导入持仓成功.")
