from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.schedulers.market.config import (
    put_close_market_event_task_config,
    toggle_market_matchmaking_task_config_0,
    toggle_market_matchmaking_task_config_1,
    toggle_market_matchmaking_task_config_2,
    toggle_market_matchmaking_task_config_3,

)


class MarketJobs:
    @classmethod
    def init(cls, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            put_close_market_event_task_config.get("func"),
            **put_close_market_event_task_config.get("cron")
        )
        scheduler.add_job(
            toggle_market_matchmaking_task_config_0.get("func"),
            **toggle_market_matchmaking_task_config_0.get("cron"),
        )
        scheduler.add_job(
            toggle_market_matchmaking_task_config_1.get("func"),
            **toggle_market_matchmaking_task_config_1.get("cron"),
        )
        scheduler.add_job(
            toggle_market_matchmaking_task_config_2.get("func"),
            **toggle_market_matchmaking_task_config_2.get("cron"),
        )
        scheduler.add_job(
            toggle_market_matchmaking_task_config_3.get("func"),
            **toggle_market_matchmaking_task_config_3.get("cron"),
        )
