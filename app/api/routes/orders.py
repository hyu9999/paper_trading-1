from starlette import status
from fastapi import APIRouter, Depends, Body, BackgroundTasks

from app.api.dependencies.database import get_repository
from app.api.dependencies.authentication import get_current_user_authorizer
from app.db.repositories.orders import OrdersRepository
from app.models.domain.users import UserInDB
from app.models.schemas.orders import OrderInCreate

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    name="orders:create-orders"
)
async def create_orders(
    background_tasks: BackgroundTasks,
    order: OrderInCreate = Body(...),
    order_repo: OrdersRepository = Depends(get_repository(OrdersRepository)),
    user: UserInDB = Depends(get_current_user_authorizer()),
):
    print(user)
