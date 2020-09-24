from app.models.domain.orders import OrderInDB
from app.models.enums import OrderTypeEnum, OrderStatusEnum
from app.models.schemas.orders import OrderInUpdateStatus
from app.services.quotes.tdx import TDXQuotes
from app.services.engines.market_engine.base import BaseMarket
from app.services.engines.user_engine import UserEngine
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import ORDER_UPDATE_STATUS_EVENT


class ChinaAMarket(BaseMarket):
    """A股市场."""
    def __init__(self, event_engine: EventEngine, user_engine: UserEngine) -> None:
        super().__init__(event_engine, user_engine)
        self.market_name = "中国A股"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识
        self.quotes_api = TDXQuotes()

    def startup(self) -> None:
        super().startup()
        self.write_log("初始化行情系统中...")
        self.quotes_api.connect_pool()
        self.write_log("初始化行情系统完成.")

    def shutdown(self) -> None:
        super().shutdown()
        self.quotes_api.close()

