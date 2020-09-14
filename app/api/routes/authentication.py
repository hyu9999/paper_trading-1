from starlette import status
from bson.errors import InvalidId
from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.errors.db import EntityDoesNotExist
from app.errors.http import InvalidLoginInput
from app.models.schemas.users import UserInCreate, UserInLogin, UserInResponse
from app.models.base import PyObjectId
from app.services import jwt


router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInResponse,
    name="auth:register"
)
async def register(
    user_create: UserInCreate,
    users_repo: UsersRepository = Depends(get_repository(UsersRepository))
) -> UserInResponse:
    user = await users_repo.create_user(**user_create.dict())
    token = jwt.create_access_token_for_user(_id=str(user.id))
    return UserInResponse(**user.dict(), token=token)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserInResponse,
    name="auth:login"
)
async def login(
    user_login: UserInLogin,
    users_repo: UsersRepository = Depends(get_repository(UsersRepository))
) -> UserInResponse:
    try:
        user = await users_repo.get_user_by_id(_id=PyObjectId(user_login.id))
    except InvalidId as InvalidIdError:
        raise InvalidLoginInput(InvalidIdError)
    except EntityDoesNotExist as EntityDoesNotExistError:
        raise InvalidLoginInput(EntityDoesNotExistError)
    else:
        token = jwt.create_access_token_for_user(_id=user_login.id)
        return UserInResponse(**user.dict(), token=token)

