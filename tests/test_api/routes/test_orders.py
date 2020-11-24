import pytest
from fastapi import FastAPI
from pytest_mock import MockerFixture
from starlette import status
from httpx import AsyncClient

from app.models.domain.orders import OrderInDB

pytestmark = pytest.mark.asyncio


TEST_ORDER_1 = {
    "symbol": "601816",
    "exchange": "SH",
    "volume": 10,
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


async def test_user_can_get_order(app: FastAPI, authorized_client: AsyncClient, order_buy_type: OrderInDB):
    response_200 = await authorized_client.request(
        "GET", app.url_path_for("orders:get-order", entrust_id=str(order_buy_type.entrust_id))
    )
    assert response_200.status_code == status.HTTP_200_OK
    entrust_id = str(order_buy_type.entrust_id)[::-1]
    response_404 = await authorized_client.request(
        "GET", app.url_path_for("orders:get-order", entrust_id=entrust_id)
    )
    assert response_404.status_code == status.HTTP_404_NOT_FOUND


async def test_user_can_get_orders(app: FastAPI, authorized_client: AsyncClient):
    response_200 = await authorized_client.request(
        "GET", app.url_path_for("orders:get-order-list")
    )
    assert response_200.status_code == status.HTTP_200_OK


async def mock_put(*args, **kwargs):
    pass


async def test_user_can_delete_entrust_order(
    app: FastAPI,
    authorized_client: AsyncClient,
    order_buy_type_status_not_done: OrderInDB,
    mocker: MockerFixture,
):
    mocker.patch("app.services.engines.market_engine.china_a_market.ChinaAMarket.put", mock_put)
    response_200 = await authorized_client.request(
        "DELETE", app.url_path_for("orders:delete-entrust-order",
                                   entrust_id=str(order_buy_type_status_not_done.entrust_id))
    )
    assert response_200.status_code == status.HTTP_200_OK
    entrust_id = str(order_buy_type_status_not_done.entrust_id)[::-1]
    response_404 = await authorized_client.request(
        "DELETE", app.url_path_for("orders:delete-entrust-order", entrust_id=entrust_id)
    )
    assert response_404.status_code == status.HTTP_404_NOT_FOUND
