from app import state, settings
from app.services.engines.event_engine import Event
from app.services.engines.event_constants import MARKET_CLOSE_EVENT
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def put_close_market_event_task():
    """触发交易市场收盘事件."""
    main_engine = state.engine
    market_close_event = Event(MARKET_CLOSE_EVENT)
    await main_engine.event_engine.put(market_close_event)


async def toggle_market_matchmaking_task():
    """切换市场引擎撮合交易开关."""
    market_engine = state.engine.market_engine
    if market_class.is_trading_time():
        await market_engine.start_matchmaking()
    else:
        await market_engine.stop_matchmaking()
