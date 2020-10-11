from typing import List
from datetime import date

from starlette import status as http_status
from fastapi import APIRouter, Depends, Body, Query

from app.api.dependencies.state import get_engine
from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.order import OrderRepository
from app.exceptions.db import EntityDoesNotExist
from app.exceptions.service import InsufficientFunds, InvalidExchange
from app.exceptions.http import InsufficientAccountFunds, InvalidOrderExchange, OrderNotFound
from app.models.types import PyObjectId
from app.models.domain.users import UserInDB
from app.models.schemas.http import HttpMessage
from app.models.enums import OrderStatusEnum, OrderTypeEnum
from app.models.schemas.orders import OrderInCreate, OrderInResponse
from app.services.engines.main_engine import MainEngine

router = APIRouter()


@router.post(
    "/",
    status_code=http_status.HTTP_201_CREATED,
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
    "/{entrust_id}",
    status_code=http_status.HTTP_200_OK,
    name="orders:get-order",
    response_model=OrderInResponse
)
async def get_order(
    entrust_id: PyObjectId,
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    try:
        order = await order_repo.get_order_by_entrust_id(entrust_id)
        return OrderInResponse(**dict(order))
    except EntityDoesNotExist:
        raise OrderNotFound(status_code=http_status.HTTP_404_NOT_FOUND)


@router.get(
    "/",
    status_code=http_status.HTTP_200_OK,
    name="orders:get-order-list",
    response_model=List[OrderInResponse]
)
async def get_order_list(
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
    status: List[OrderStatusEnum] = Query(None, description="订单状态"),
    start_date: date = Query(None, description="开始时间"),
    end_date: date = Query(None, description="结束时间"),
):
    orders = await order_repo.get_orders(user_id=user.id, status=status, start_date=start_date, end_date=end_date)
    return [OrderInResponse(**dict(order)) for order in orders]


@router.delete(
    "/entrust_orders/{entrust_id}",
    status_code=http_status.HTTP_200_OK,
    name="orders:delete-entrust-order",
    response_model=HttpMessage
)
async def delete_entrust_order(
    entrust_id: PyObjectId,
    engine: MainEngine = Depends(get_engine),
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    try:
        order = await order_repo.get_order_by_entrust_id(entrust_id)
    except EntityDoesNotExist:
        raise OrderNotFound(status_code=http_status.HTTP_404_NOT_FOUND)
    else:
        order_cancel = OrderInCreate(**order.dict())
        order_cancel.order_type = OrderTypeEnum.CANCEL
        await order_repo.create_order(**order_cancel.dict(), **{"user_id": user.id})
        await engine.market_engine.put(order)
        return HttpMessage(text="成功提交取消委托订单请求.")
