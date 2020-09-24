from typing import List

from starlette import status
from fastapi import APIRouter, Depends, Body

from app.api.dependencies.state import get_engine
from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.order import OrderRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.service import InsufficientFunds, InvalidExchange
from app.exceptions.http import InsufficientAccountFunds, InvalidOrderExchange, OrderNotFound
from app.models.types import PyObjectId
from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate, OrderInResponse
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


@router.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    name="orders:get-order",
    response_model=OrderInResponse
)
async def get_order(
    order_id: PyObjectId,
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    try:
        order = await order_repo.get_order_by_order_id(order_id)
        return OrderInResponse(**dict(order))
    except EntityDoesNotExist:
        raise OrderNotFound(status_code=404)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    name="orders:get-order-list",
    response_model=List[OrderInResponse]
)
async def get_order_list(
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    orders = await order_repo.get_orders_by_user_id(user.id)
    return [OrderInResponse(**dict(order)) for order in orders]
