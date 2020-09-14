from starlette import status
from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.models.schemas.users import UserInCreate, UserInResponse


router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInResponse,
    name="auth:create-user"
)
async def create_user(
    user_create: UserInCreate,
    users_repo: UsersRepository = Depends(get_repository(UsersRepository))
) -> UserInResponse:
    user = await users_repo.create_user(**user_create.dict())
    return UserInResponse(**user.dict())

