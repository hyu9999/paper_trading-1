from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.schedulers.user.config import (
    sync_dividend_data_task_config,
    sync_user_assets_in_init_task_config,
    sync_user_assets_task_config,
)


class UserJobs:
    @classmethod
    def init(cls, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            sync_user_assets_task_config.get("func"),
            **sync_user_assets_task_config.get("cron")
        )
        scheduler.add_job(
            sync_user_assets_in_init_task_config.get("func"),
            **sync_user_assets_in_init_task_config.get("cron")
        )
        scheduler.add_job(
            sync_dividend_data_task_config.get("func"),
            **sync_dividend_data_task_config.get("cron")
        )
