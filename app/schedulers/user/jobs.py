from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.schedulers.user.config import sync_user_assets_config, sync_user_assets_in_init_config


class UserJobs:
    @classmethod
    def init(cls, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(sync_user_assets_config.get("func"), **sync_user_assets_config.get("cron"))
        scheduler.add_job(sync_user_assets_in_init_config.get("func"), **sync_user_assets_in_init_config.get("cron"))
