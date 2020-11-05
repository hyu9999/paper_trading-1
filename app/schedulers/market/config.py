from datetime import datetime, timedelta

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

trading_time = []
for period in market_class.TRADING_PERIOD:
    trading_time.append(period.get("start"))
    trading_time.append(period.get("end"))
trading_time_hours = [str(tt.hour) for tt in trading_time]
trading_time_minutes = [str(tt.minute) for tt in trading_time]
trading_time_seconds = [str(tt.second) for tt in trading_time]

toggle_market_matchmaking_task_config_0 = {
    "func": toggle_market_matchmaking_task,
    "cron": {
        "id": "切换市场引擎撮合交易开关",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": trading_time_hours[0],
        "minute": trading_time_minutes[0],
        "second": trading_time_seconds[0],
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

toggle_market_matchmaking_task_config_1 = {
    "func": toggle_market_matchmaking_task,
    "cron": {
        "id": "切换市场引擎撮合交易开关",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": trading_time_hours[1],
        "minute": trading_time_minutes[1],
        "second": trading_time_seconds[1],
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

toggle_market_matchmaking_task_config_2 = {
    "func": toggle_market_matchmaking_task,
    "cron": {
        "id": "切换市场引擎撮合交易开关",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": trading_time_hours[2],
        "minute": trading_time_minutes[2],
        "second": trading_time_seconds[2],
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}

toggle_market_matchmaking_task_config_3 = {
    "func": toggle_market_matchmaking_task,
    "cron": {
        "id": "切换市场引擎撮合交易开关",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": trading_time_hours[3],
        "minute": trading_time_minutes[3],
        "second": trading_time_seconds[3],
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
