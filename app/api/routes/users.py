from starlette import status
from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.schemas.users import ListOfUserInResponse


router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ListOfUserInResponse,
    name="users:list-users"
)
async def list_users(
    users_repo: UsersRepository = Depends(get_repository(UsersRepository))
) -> ListOfUserInResponse:
    users = await users_repo.get_users_list()
    return ListOfUserInResponse(users=users, count=len(users))
