import pytest
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas.users import UserInResponse


pytestmark = pytest.mark.asyncio


async def test_user_success_registration(app: FastAPI, client: AsyncClient, db: AsyncIOMotorDatabase) -> None:
    json = {
        "capital": 1000000.00
    }
    response = await client.request("POST", app.url_path_for("auth:create-user"), json=json)
    assert response.status_code == status.HTTP_201_CREATED
    response.json()["_id"] = response.json().pop("_id")
    user = UserInResponse(**response.json())
    assert user.capital == 1000000.00
    assert user.cash == 1000000.00
    assert user.assets == 1000000.00
