import pytest
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient

from app.models.domain.users import UserInDB
from app.models.schemas.users import ListOfUserInResponse, UserInResponse


pytestmark = pytest.mark.asyncio


async def test_user_get_account_by_id(app: FastAPI, client: AsyncClient, test_user_scope_func: UserInDB) -> None:
    response = await client.request("GET", app.url_path_for("users:get-user", user_id=str(test_user_scope_func.id)))
    assert response.status_code == status.HTTP_200_OK
    user = UserInResponse(**response.json())
    assert user


async def test_user_can_get_account_list(app: FastAPI, client: AsyncClient) -> None:
    response = await client.request("GET", app.url_path_for("users:list-users"))
    assert response.status_code == status.HTTP_200_OK
    list_user = ListOfUserInResponse(**response.json())
    assert len(list_user.users) == list_user.count
