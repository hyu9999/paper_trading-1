from starlette import status
from fastapi import APIRouter, Depends, Body, Request, BackgroundTasks

from app.api.dependencies.database import get_repository
from app.db.repositories.orders import OrdersRepository

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="orders:create-orders"
)
async def create_orders(
    request: Request,
    background_task: BackgroundTasks
    # order: OrderInCreate = Body(...),
    # order_repo: OrdersRepository = Depends(get_repository(OrdersRepository)),
    # user: UserInDB = Depends(get_current_user_authorizer()),
):
    await request.app.state.engine.on_foo(background_task)

