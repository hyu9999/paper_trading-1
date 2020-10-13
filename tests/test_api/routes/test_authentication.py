import pytest
from bson import Decimal128
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient

from app.models.schemas.users import UserInResponse
from app.models.domain.users import UserInDB


pytestmark = pytest.mark.asyncio


async def test_user_success_registration(app: FastAPI, client: AsyncClient) -> None:
    json = {
        "capital": 1000000.00,
        "desc": None
    }
    response = await client.request("POST", app.url_path_for("auth:register"), json=json)
    assert response.status_code == status.HTTP_201_CREATED
    user = UserInResponse(**response.json())
    assert user.capital == Decimal128("1000000.0")
    assert user.cash == Decimal128("1000000.0")
    assert user.assets == Decimal128("1000000.0")


async def test_user_can_login(app: FastAPI, client: AsyncClient, test_user: UserInDB) -> None:
    json = {"id": str(test_user.id)}
    response = await client.request("POST", app.url_path_for("auth:login"), json=json)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["token"]


@pytest.mark.parametrize(
    "user_id, status_code",
    [
        ("5f5f2478483c3123207d62b", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("5f5f2478483c3123207d62b2", status.HTTP_400_BAD_REQUEST)
    ],
)
async def test_user_login_error_can_captured(
        app: FastAPI, client: AsyncClient, user_id: str, status_code: status
) -> None:
    json = {"id": user_id}
    response = await client.request("POST", app.url_path_for("auth:login"), json=json)
    assert response.status_code == status_code
