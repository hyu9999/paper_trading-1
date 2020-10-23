import pytest

from app.services.quotes.jq import JQQuotes

pytestmark = pytest.mark.asyncio


@pytest.fixture
def jq_api():
    return JQQuotes()


async def test_jq_api_can_format_stock_codes(jq_api: JQQuotes):
    jq_code = jq_api.format_stock_code("601816.SH")
    assert jq_code == "601816.XSHG"
