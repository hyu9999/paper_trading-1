from datetime import datetime
from contextlib import contextmanager

from jqdatasdk import auth, logout
from jqdatasdk import get_ticks as jq_get_ticks

from app import settings
from app.models.enums import ExchangeEnum
from app.models.schemas.quotes import Quotes
from app.services.quotes.base import BaseQuotes


class JQQuotes(BaseQuotes):
    EXCHANGE_MAPPING = {"SH": "XSHG", "SZ": "XSHE"}

    @contextmanager
    def connect_api(self):
        auth(str(settings.jqdata_user), str(settings.jqdata_password))
        yield
        logout()

    async def get_ticks(self, code: str) -> Quotes:
        """获取股票Ticks数据.

        Parameters
        ----------
        code : 600001.SH
        """
        jq_code = self.format_stock_code(code)
        str_of_today = str(datetime.today().date())
        with self.connect_api():
            df_ticks = jq_get_ticks(security=jq_code, count=1, end_dt=str_of_today)
        return self._format_quotes(df_ticks.to_dict("records")[0], code=code)

    @classmethod
    def format_stock_code(cls, code: str) -> str:
        symbol, exchange = code.split(".")
        return f"{symbol}.{cls.EXCHANGE_MAPPING[exchange]}"

    @classmethod
    def _format_quotes(cls, quotes_dict: dict, code: str) -> Quotes:
        symbol, exchange = code.split(".")
        return Quotes(
            exchange=ExchangeEnum.SH if exchange == "SH" else ExchangeEnum.SZ,
            symbol=symbol,
            price=quotes_dict["current"],
            high=quotes_dict["high"],
            low=quotes_dict["low"],
            time=quotes_dict["time"],
            bid1_p=quotes_dict.get("b1_p"),
            bid2_p=quotes_dict.get("b2_p"),
            bid3_p=quotes_dict.get("b3_p"),
            bid4_p=quotes_dict.get("b4_p"),
            bid5_p=quotes_dict.get("b5_p"),
            ask1_p=quotes_dict.get("a1_p"),
            ask2_p=quotes_dict.get("a2_p"),
            ask3_p=quotes_dict.get("a3_p"),
            ask4_p=quotes_dict.get("a4_p"),
            ask5_p=quotes_dict.get("a5_p"),
            bid1_v=quotes_dict.get("b1_v"),
            bid2_v=quotes_dict.get("b2_v"),
            bid3_v=quotes_dict.get("b3_v"),
            bid4_v=quotes_dict.get("b4_v"),
            bid5_v=quotes_dict.get("b5_v"),
            ask1_v=quotes_dict.get("a1_v"),
            ask2_v=quotes_dict.get("a2_v"),
            ask3_v=quotes_dict.get("a3_v"),
            ask4_v=quotes_dict.get("a4_v"),
            ask5_v=quotes_dict.get("a5_v"),
        )
