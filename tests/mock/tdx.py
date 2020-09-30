from app.models.schemas.quotes import Quotes
from app.services.quotes.base import BaseQuotes
from tests.json.quotes import quotes_json


class TDXQuotesMocker(BaseQuotes):
    SOCKET_TIMEOUT = 0.05
    EXCHANGE_MAPPING = {"SH": 1, "SZ": 0}

    def __init__(self) -> None:
        pass

    async def connect_pool(self) -> None:
        pass

    async def get_ticks(self, stock_code) -> Quotes:
        quotes_json.update({"symbol": stock_code.split(".")[0]})
        quotes_json.update({"exchange": stock_code.split(".")[1]})
        return Quotes(**quotes_json)

    async def close(self) -> None:
        pass
