import pytest

from app.schedulers.liquidation.func import liquidate_dividend_task

pytestmark = pytest.mark.asyncio


async def test_liquidate_dividend_task(initialized_app):
    await liquidate_dividend_task()
