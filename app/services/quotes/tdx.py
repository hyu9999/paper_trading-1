import socket
from time import perf_counter
from typing import List, Tuple
from collections import OrderedDict, defaultdict

from pytdx.config.hosts import hq_hosts
from pytdx.hq import TdxHq_API
from pytdx.pool.hqpool import TdxHqPool_API
from pytdx.pool.ippool import AvailableIPPool


class TDXQuotes:
    # 测试可用性时用到的socket超时时间
    SOCKET_TIMEOUT = 0.05
    EXCHANGE_MAPPING = {"SH": 1, "SZ": 0}

    def __init__(self) -> None:
        self.api = None

    def connect_pool(self) -> None:
        """连接到通达信行情池"""
        addr = self.get_available_addr()
        ip_pool = AvailableIPPool(TdxHq_API, addr[:5])
        primary_ip, hot_backup_ip = ip_pool.sync_get_top_n(2)
        self.api = TdxHqPool_API(TdxHq_API, ip_pool)
        self.api.connect(primary_ip, hot_backup_ip)

    @classmethod
    def get_available_addr(cls) -> List[tuple]:
        """获取可用的行情源，按可用性排序"""
        addr_speed_dict = defaultdict(list)
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
        return [(v[1], v[2]) for k, v in sorted(addr_speed_dict.items(), key=lambda kv: kv[0])]

    def get_ticks(self, code: str) -> OrderedDict:
        """
        获取股票Ticks数据

        Parameters:
            code: 600001.SH
        """
        tdx_code = self.format_stock_code(code)
        data = self.api.get_security_quotes(tdx_code)
        return data

    @classmethod
    def format_stock_code(cls, code: str) -> Tuple[int, str]:
        """
        转化股票代码为通达信格式

        Parameters:
            code: 600001.SH
        """
        symbol, exchange = code.split(".")
        return cls.EXCHANGE_MAPPING[exchange], symbol

    def close(self) -> None:
        self.api.disconnect()
