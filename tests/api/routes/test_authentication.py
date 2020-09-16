import pytest
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient

from app.models.schemas.users import UserInResponse
from app.models.domain.users import User


pytestmark = pytest.mark.asyncio


async def test_user_success_registration(app: FastAPI, client: AsyncClient) -> None:
    json = {
        "capital": 1000000.00
    }
    response = await client.request("POST", app.url_path_for("auth:register"), json=json)
    assert response.status_code == status.HTTP_201_CREATED
    response.json()["_id"] = response.json().pop("_id")
    user = UserInResponse(**response.json())
    assert user.capital == 1000000.00
    assert user.cash == 1000000.00
    assert user.assets == 1000000.00


async def test_user_can_login(app: FastAPI, client: AsyncClient, test_user: User) -> None:
    json = {"id": str(test_user.id)}
    response = await client.request("POST", app.url_path_for("auth:login"), json=json)
    assert response.status_code == status.HTTP_200_OK
    response.json()["_id"] = response.json().pop("_id")
    user = UserInResponse(**response.json())
    assert str(user.id) == json["id"]


@pytest.mark.parametrize(
    "user_id",
    ("5f5f2478483c3123207d62b", "5f5f2478483c3123207d62b2"),
)
async def test_user_login_error_can_captured(app: FastAPI, client: AsyncClient, user_id: str) -> None:
    json = {"id": user_id}
    response = await client.request("POST", app.url_path_for("auth:login"), json=json)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"] == 10001
