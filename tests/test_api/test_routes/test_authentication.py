import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import HTTP_201_CREATED

pytestmark = pytest.mark.asyncio


async def test_user_register(app: FastAPI, client: AsyncClient) -> None:
    register_json = {"capital": 1000000}
    response = await client.post(app.url_path_for("auth:register"), json=register_json)
    assert response.status_code == HTTP_201_CREATED
