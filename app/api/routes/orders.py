from starlette import status
from fastapi import APIRouter, Depends, Body

from app.api.dependencies.state import get_engine
from app.api.dependencies.authentication import get_current_user_authorizer
from app.exceptions.service import InsufficientFunds, InvalidExchange
from app.exceptions.http import InsufficientAccountFunds, InvalidOrderExchange
from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate
from app.services.engines.main_engine import MainEngine

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="orders:create-order"
)
async def create_order(
    order: OrderInCreate = Body(...),
    engine: MainEngine = Depends(get_engine),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    try:
        return await engine.on_order_arrived(order, user)
    except InsufficientFunds:
        raise InsufficientAccountFunds
    except InvalidExchange:
        raise InvalidOrderExchange
