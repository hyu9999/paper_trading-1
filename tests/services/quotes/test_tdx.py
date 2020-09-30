import pytest

from app.exceptions.service import NotEnoughAvailableAddr
from app.services.quotes.tdx import TDXQuotes

pytestmark = pytest.mark.asyncio


def test_user_can_get_enough_addr():
    try:
        addr_list = TDXQuotes.get_available_addr()
    except NotEnoughAvailableAddr:
        pass
    else:
        # 确保返回地址的数量大于5
        assert len(addr_list) > 5
