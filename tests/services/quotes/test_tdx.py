import pytest

from app.services.quotes.tdx import TDXQuotes

pytestmark = pytest.mark.asyncio


def test_user_can_get_enough_addr():
    addr_list = TDXQuotes.get_available_addr()
    # 确保返回地址的数量大于5
    assert len(addr_list) > 5


async def test_user_can_get_stock_ticks():
    tdx = TDXQuotes()
    await tdx.connect_pool()
    quotes = await tdx.get_ticks("601816.SH")
    await tdx.close()
    assert quotes.exchange.value == "SH"
    assert quotes.symbol == "601816"
