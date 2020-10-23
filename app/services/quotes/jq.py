import asyncio
import logging
from typing import List
from io import StringIO
from datetime import datetime

import httpx
import pandas as pd
from loguru import logger

from app import settings
from app.models.enums import ExchangeEnum
from app.models.schemas.quotes import Quotes
from app.services.quotes.base import BaseQuotes
from app.exceptions.service import GetQuotesFailed

asyncio.log.logger.setLevel(logging.ERROR)


class JQQuotes(BaseQuotes):
    EXCHANGE_MAPPING = {"SH": "XSHG", "SZ": "XSHE"}
    API_URL = "https://dataapi.joinquant.com/apis"

    @classmethod
    async def _get_token(cls) -> str:
        async with httpx.AsyncClient() as client:
            json = {
                "method": "get_token",
                "mob": str(settings.jqdata_user),
                "pwd": settings.jqdata_password
            }
            response = await client.post(cls.API_URL, json=json)
            return response.text

    @classmethod
    async def _http_wrap(cls, json: dict) -> pd.DataFrame:
        json["token"] = await cls._get_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(cls.API_URL, json=json)
            response_text = response.text
            if response_text[:5] == "error":
                raise GetQuotesFailed(response_text)
            quotes_content = StringIO(response_text)
            df_quotes = pd.read_csv(quotes_content)
            return df_quotes

    async def get_ticks(self, code: str) -> Quotes:
        """获取股票Ticks数据.

        Parameters
        ----------
        code : 600001.SH
        """
        jq_code = self.format_stock_code(code)
        str_of_today = str(datetime.today().date())
        retry_count = 0
        while retry_count < settings.quotes_max_retry:
            try:
                json = {
                    "method": "get_ticks",
                    "code": jq_code,
                    "end_date": str_of_today,
                    "count": 1
                }
                df_quotes = await asyncio.wait_for(self._http_wrap(json=json), settings.quotes_api_timeout)
            except (asyncio.futures.TimeoutError, GetQuotesFailed) as e:
                logger.info(f"获取股票[{code}]行情失败, {e}.")
                retry_count += 1
                logger.info(f"正在重新获取股票[{code}]行情[{retry_count}/{settings.quotes_max_retry}]...")
            else:
                return self._format_quotes(df_quotes.to_dict("records")[0], code=code)
        logger.error(f"获取股票[{code}]错误.")
        raise TimeoutError(f"获取股票[{code}]行情错误.")

    async def get_current_tick(self, code_list: List[str]) -> List[Quotes]:
        """获取股票列表Ticks数据."""
        jq_code_list = [self.format_stock_code(jq_code) for jq_code in code_list]
        retry_count = 0
        while retry_count < settings.quotes_max_retry:
            try:
                json = {
                    "method": "get_current_ticks2",
                    "code": ",".join(jq_code_list)
                }
                df_quotes_list = await asyncio.wait_for(self._http_wrap(json=json), settings.quotes_api_timeout)
            except (asyncio.futures.TimeoutError, GetQuotesFailed) as e:
                logger.info(f"获取股票行情列表失败, {e}.")
                retry_count += 1
                logger.info(f"获取股票行情列表[{retry_count}/{settings.quotes_max_retry}]...")
            else:
                return [self._format_quotes(row, code=row["0"]) for _, row in df_quotes_list.reset_index().iterrows()]
        logger.error("获取股票行情列表错误.")
        raise TimeoutError("获取股票行情列表错误.")

    @classmethod
    def format_stock_code(cls, code: str) -> str:
        symbol, exchange = code.split(".")
        return f"{symbol}.{cls.EXCHANGE_MAPPING[exchange]}"

    @classmethod
    def _format_quotes(cls, quotes_dict: dict, code: str) -> Quotes:
        symbol, exchange = code.split(".")
        return Quotes(
            exchange=ExchangeEnum.SH if exchange == "SH" or cls.EXCHANGE_MAPPING["SH"] else ExchangeEnum.SZ,
            symbol=symbol,
            price=quotes_dict["current"],
            high=quotes_dict["high"],
            low=quotes_dict["low"],
            time=quotes_dict.get("time"),
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
