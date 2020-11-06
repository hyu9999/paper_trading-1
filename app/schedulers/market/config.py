from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger

from app import settings
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING
from app.schedulers.market.func import put_close_market_event_task, toggle_market_matchmaking_task

market_class = MARKET_NAME_MAPPING[settings.service.market]

put_close_market_event_task_config = {
    "func": put_close_market_event_task,
    "cron": {
        "id": "向事件引擎推送交易市场收盘事件",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": market_class.CLOSE_MARKET_TIME.hour,
        "minute": market_class.CLOSE_MARKET_TIME.minute,
        "second": market_class.CLOSE_MARKET_TIME.second,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

trading_time_list = []
for period in market_class.TRADING_PERIOD:
    trading_time_list.append(period.get("start"))
    trading_time_list.append(period.get("end"))

toggle_market_matchmaking_task_config = {
    "func": toggle_market_matchmaking_task,
    "cron": OrTrigger([CronTrigger(
        day_of_week="0-4",
        hour=trading_time.hour,
        minute=trading_time.minute,
        second=1,
        timezone="Asia/Shanghai",
    ) for trading_time in trading_time_list])
}
