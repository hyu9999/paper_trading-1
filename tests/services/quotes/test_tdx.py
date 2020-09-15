from app.services.quotes.tdx import TDXQuotes


def test_user_can_get_enough_addr():
    addr_list = TDXQuotes.get_available_addr()
    # 确保返回地址的数量大于5
    assert len(addr_list) > 5


def test_user_can_get_stock_ticks():
    tdx = TDXQuotes()
    tdx.connect_pool()
    data = tdx.get_ticks("601816.SH")
    assert data
    tdx.close()
