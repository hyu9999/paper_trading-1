import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

pytestmark = pytest.mark.asyncio


async def test_user_can_get_position(app: FastAPI, authorized_client: AsyncClient):
    response_200 = await authorized_client.request(
        "GET", app.url_path_for("position:get-position-list")
    )
    assert response_200.status_code == status.HTTP_200_OK
