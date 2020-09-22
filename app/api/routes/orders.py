from starlette import status
from fastapi import APIRouter, Depends, Body, Request

from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.order import OrderRepository
from app.exceptions.service import InsufficientFunds
from app.exceptions.http import InsufficientAccountFunds
from app.models.schemas.orders import OrderInCreate
from app.models.domain.users import UserInDB

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="orders:create-order"
)
async def create_order(
    request: Request,
    order: OrderInCreate = Body(...),
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    try:
        return await request.app.state.engine.on_order_arrived(order, user)
    except InsufficientFunds:
        raise InsufficientAccountFunds
