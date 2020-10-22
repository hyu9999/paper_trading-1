import socket
from time import perf_counter
from typing import List, Tuple

from loguru import logger
from pytdx.config.hosts import hq_hosts
from pytdx.hq import TdxHq_API
from pytdx.pool.hqpool import TdxHqPool_API
from pytdx.pool.ippool import AvailableIPPool

from app.exceptions.service import NotEnoughAvailableAddr
from app.models.enums import ExchangeEnum
from app.models.schemas.quotes import Quotes
from app.services.quotes.base import BaseQuotes


class TDXQuotes(BaseQuotes):
    # 测试可用性时用到的socket超时时间
    SOCKET_TIMEOUT = 0.05
    EXCHANGE_MAPPING = {"SH": 1, "SZ": 0}

    def __init__(self) -> None:
        addr = self.get_available_addr()
        self.ip_pool = AvailableIPPool(TdxHq_API, addr[:5])
        self.api: TdxHqPool_API = TdxHqPool_API(TdxHq_API, self.ip_pool)

    async def connect_pool(self) -> None:
        """连接到通达信行情池."""
        logger.info("连接行情系统中...")
        primary_ip, hot_backup_ip = self.ip_pool.sync_get_top_n(2)
        self.api.connect(primary_ip, hot_backup_ip)
        logger.info("行情系统连接成功.")

    @classmethod
    def get_available_addr(cls) -> List[tuple]:
        """获取可用的行情地址，按可用性排序."""
        addr_speed_dict = {}
        for addr in hq_hosts:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(cls.SOCKET_TIMEOUT)
            host, port = addr[1:]
            start = perf_counter()
            try:
                sock.connect((host, port))
                end = perf_counter()
                speed = end-start
            except (socket.timeout, ConnectionRefusedError):
                speed = cls.SOCKET_TIMEOUT
            addr_speed_dict[speed] = addr
        if len(addr_speed_dict) < 6:
            raise NotEnoughAvailableAddr
        return [(v[1], v[2]) for k, v in sorted(addr_speed_dict.items(), key=lambda kv: kv[0])]

    async def get_ticks(self, code: str) -> Quotes:
        """获取股票Ticks数据.

        Parameters
        ----------
        code : 600001.SH
        """
        tdx_code = self.format_stock_code(code)
        api_quotes = self.api.get_security_quotes(tdx_code)
        return await self._format_quotes(api_quotes[0])

    @classmethod
    def format_stock_code(cls, code: str) -> Tuple[int, str]:
        """转化股票代码为通达信格式.

        Parameters
        ----------
        code : 600001.SH
        """
        symbol, exchange = code.split(".")
        return cls.EXCHANGE_MAPPING[exchange], symbol

    @classmethod
    async def _format_quotes(cls, api_quotes: dict) -> Quotes:
        return Quotes(
            exchange=ExchangeEnum.SH if api_quotes["market"] == 1 else ExchangeEnum.SZ,
            symbol=api_quotes["code"],
            price=api_quotes["price"],
            last_close=api_quotes["last_close"],
            open=api_quotes["open"],
            high=api_quotes["high"],
            low=api_quotes["low"],
            bid1_p=api_quotes.get("bid1"),
            bid2_p=api_quotes.get("bid2"),
            bid3_p=api_quotes.get("bid3"),
            bid4_p=api_quotes.get("bid4"),
            bid5_p=api_quotes.get("bid5"),
            ask1_p=api_quotes.get("ask1"),
            ask2_p=api_quotes.get("ask2"),
            ask3_p=api_quotes.get("ask3"),
            ask4_p=api_quotes.get("ask4"),
            ask5_p=api_quotes.get("ask5"),
            bid1_v=api_quotes.get("bid_vol1"),
            bid2_v=api_quotes.get("bid_vol2"),
            bid3_v=api_quotes.get("bid_vol3"),
            bid4_v=api_quotes.get("bid_vol4"),
            bid5_v=api_quotes.get("bid_vol5"),
            ask1_v=api_quotes.get("ask_vol1"),
            ask2_v=api_quotes.get("ask_vol2"),
            ask3_v=api_quotes.get("ask_vol3"),
            ask4_v=api_quotes.get("ask_vol4"),
            ask5_v=api_quotes.get("ask_vol5"),
        )

    async def close(self) -> None:
        # 当uvicorn处于热重载模式并通过命令行关闭应用时，执行api.close方法会触发此异常
        try:
            self.api.disconnect()
        except AttributeError:
            pass
