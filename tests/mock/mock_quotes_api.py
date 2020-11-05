from hq2redis.models import StockTicks

from app.models.base import get_utc_now
from tests.json.quotes import quotes_json


class QuotesAPIMocker:
    async def get_stock_ticks(self, stock_code) -> StockTicks:
        symbol, exchange = stock_code.split(".")
        quotes_json.update({"symbol": symbol})
        quotes_json.update({"exchange": exchange})
        quotes_json.update({"current": quotes_json["bid1_p"]})
        quotes_json.update({"timestamp": get_utc_now()})
        return StockTicks(**quotes_json)

    async def startup(self):
        pass

    async def shutdown(self):
        pass
