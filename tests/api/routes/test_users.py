import pytest
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient
from dynaconf import Dynaconf

from app.models.schemas.users import ListOfUserInResponse


pytestmark = pytest.mark.asyncio


async def test_user_can_get_account_list(app: FastAPI, client: AsyncClient, settings: Dynaconf) -> None:
    response = await client.request("GET", app.url_path_for("users:list-users"))
    assert response.status_code == status.HTTP_200_OK
    list_user = ListOfUserInResponse(**response.json())
    assert len(list_user.users) == list_user.count
