from app.schedulers.liquidation.func import (
    liquidate_dividend_flow_task,
    liquidate_dividend_task,
    liquidate_dividend_tax_task,
)

liquidate_dividend_config = {
    "func": liquidate_dividend_task,
    "cron": {
        "id": "清算分红",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 4,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


liquidate_dividend_tax_config = {
    "func": liquidate_dividend_tax_task,
    "cron": {
        "id": "清算红利税",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 4,
        "minute": 30,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}


liquidate_dividend_flow_config = {
    "func": liquidate_dividend_flow_task,
    "cron": {
        "id": "清算分红流水",
        "trigger": "cron",
        "day_of_week": "0-4",
        "hour": 5,
        "minute": 0,
        "second": 0,
        "timezone": "Asia/Shanghai",
        "replace_existing": True,
        "misfire_grace_time": 900,
    },
}
