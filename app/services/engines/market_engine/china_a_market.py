from app.models.domain.orders import OrderInDB
from app.models.schemas.orders import OrderInCache
from app.models.enums import OrderTypeEnum, OrderStatusEnum
from app.models.schemas.event_payload import OrderInUpdateStatusPayload
from app.services.quotes.tdx import TDXQuotes
from app.services.engines.market_engine.base import BaseMarket
from app.services.engines.event_engine import EventEngine, Event
from app.services.engines.event_constants import ORDER_UPDATE_STATUS_EVENT


class ChinaAMarket(BaseMarket):
    """A股市场."""
    def __init__(self, event_engine: EventEngine) -> None:
        super().__init__(event_engine)
        self.market_name = "中国A股"     # 交易市场名称
        self.exchange_symbols = ["SH", "SZ"]    # 交易市场标识
        self.quotes_api = TDXQuotes()

    def startup(self) -> None:
        super().startup()
        self.quotes_api.connect_pool()

    def shutdown(self) -> None:
        super().shutdown()
        self.quotes_api.close()

    async def put_order(self, order: OrderInDB) -> None:
        # 取消订单
        if order.order_type == OrderTypeEnum.CANCEL.value:
            pass
        # 清算订单
        elif order.order_type == OrderTypeEnum.LIQUIDATION.value:
            pass
        else:
            await self.exchange_validation(order)
            payload = OrderInUpdateStatusPayload(id=order.id, status=OrderStatusEnum.WAITING)
            event = Event(ORDER_UPDATE_STATUS_EVENT, payload)
            self.event_engine.put(event)
            self.write_log(f"收到订单:{order.order_id}.")
            order_in_cache_dict = dict(order)
            order_in_cache_dict.update({"price": str(order.price)})
            order_in_cache_dict.update({"order_id": str(order.order_id)})
            self.entrust_queue.put(OrderInCache(**order_in_cache_dict))
