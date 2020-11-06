from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.schedulers.market.config import (
    put_close_market_event_task_config,
    toggle_market_matchmaking_task_config,
)


class MarketJobs:
    @classmethod
    def init(cls, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            put_close_market_event_task_config.get("func"),
            **put_close_market_event_task_config.get("cron")
        )
        scheduler.add_job(
            toggle_market_matchmaking_task_config.get("func"),
            toggle_market_matchmaking_task_config.get("cron"),
        )
