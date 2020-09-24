from starlette import status
from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.user import UserRepository
from app.models.schemas.users import ListOfUserInResponse

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ListOfUserInResponse,
    name="users:list-users"
)
async def list_users(
    user_repo: UserRepository = Depends(get_repository(UserRepository))
) -> ListOfUserInResponse:
    users = await user_repo.get_users_list()
    return ListOfUserInResponse(users=users, count=len(users))
