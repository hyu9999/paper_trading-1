import pytest
from fastapi import FastAPI
from starlette import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


TEST_ORDER_1 = {
    "symbol": "601816",
    "exchange": "SH",
    "quantity": 10,
    "price": 0,
    "order_type": "buy",
    "trade_type": "T0",
}


@pytest.mark.parametrize(
    "order",
    [TEST_ORDER_1],
)
async def test_user_can_create_order(app: FastAPI, authorized_client: AsyncClient, order: dict) -> None:
    response = await authorized_client.request("POST", app.url_path_for("orders:create-order"), json=order)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["entrust_id"]
