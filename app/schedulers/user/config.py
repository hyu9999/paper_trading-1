from datetime import datetime, timedelta

from app.schedulers.user.func import sync_user_assets_task

sync_user_assets_task_config = {
    "func": sync_user_assets_task,
    "cron": {
        "id": "同步用户资产数据相关数据(定时开启)",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 9,
        "minute": 30,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


sync_user_assets_in_init_task_config = {
    "func": sync_user_assets_task,
    "cron": {
        "id": "同步用户资产相关数据(中途开启)",
        "trigger": "cron",
        "day_of_week": "0-4",
        "next_run_time": datetime.now() + timedelta(seconds=2),
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
