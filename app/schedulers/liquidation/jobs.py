from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.schedulers.liquidation.config import (
    liquidate_dividend_config,
    liquidate_dividend_flow_config,
    liquidate_dividend_tax_config,
)


class LiquidationJobs:
    @classmethod
    def init(cls, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            liquidate_dividend_config.get("func"),
            **liquidate_dividend_config.get("cron")
        )

        scheduler.add_job(
            liquidate_dividend_flow_config.get("func"),
            **liquidate_dividend_flow_config.get("cron")
        )

        scheduler.add_job(
            liquidate_dividend_tax_config.get("func"),
            **liquidate_dividend_tax_config.get("cron")
        )
