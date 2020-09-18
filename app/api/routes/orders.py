from starlette import status
from fastapi import APIRouter, Depends, Body, Request, BackgroundTasks

from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.order import OrderRepository
from app.models.schemas.orders import OrderInCreate
from app.models.domain.users import UserInDB

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="orders:create-orders"
)
async def create_orders(
    request: Request,
    background_task: BackgroundTasks,
    order: OrderInCreate = Body(...),
    order_repo: OrderRepository = Depends(get_repository(OrderRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    await request.app.state.engine.on_order_arrived(order, user, background_task)
    return 10
