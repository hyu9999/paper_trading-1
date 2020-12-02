from apscheduler.schedulers.asyncio import AsyncIOScheduler

from loguru import logger

from app.schedulers.user.jobs import UserJobs
from app.schedulers.market.jobs import MarketJobs

scheduler = AsyncIOScheduler()


async def load_jobs():
    init_scheduler_options = {
    }
    scheduler.configure(**init_scheduler_options)
    logger.info("正在加载定时任务...")
    UserJobs.init(scheduler)
    MarketJobs.init(scheduler)
    logger.info("加载定时任务完成.")

    logger.info("正在启动定时任务中...")
    scheduler.start()
    logger.info("定时任务启动完成.")


async def load_jobs_with_lock():
    try:
        import atexit
        import fcntl
    except ImportError:
        await load_jobs()
    else:
        f = open("scheduler.lock", "wb")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        await load_jobs()

        def unlock():
            fcntl.flock(f, fcntl.LOCK_UN)
            f.close()
        atexit.register(unlock)


async def stop_jobs():
    scheduler.remove_all_jobs()
