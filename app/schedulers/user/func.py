import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

import pandas as pd
import sqlalchemy.dialects
from sqlalchemy import create_engine

from app import settings, state
from app.db.cache.position import PositionCache
from app.db.cache.user import UserCache
from app.db.repositories.dividend_records import DividendRecordsRepository
from app.db.repositories.statement import StatementRepository
from app.db.utils import codec_option
from app.models.domain.dividend_records import DividendRecordsInDB
from app.models.enums import TradeCategoryEnum
from app.models.types import PyDecimal
from app.services.engines.market_engine.constant import MARKET_NAME_MAPPING

market_class = MARKET_NAME_MAPPING[settings.service.market]


async def sync_user_assets_task():
    """同步用户资产相关数据."""
    user_cache = UserCache(state.user_redis_pool)
    user_engine = state.engine.user_engine
    start_time = datetime.combine(date.today(), market_class.OPEN_MARKET_TIME)
    end_time = datetime.combine(date.today(), market_class.CLOSE_MARKET_TIME)
    users = await user_cache.get_all_user()
    while start_time < datetime.now() < end_time:
        await asyncio.gather(
            *(user_engine.liquidate_user_position(user.id) for user in users)
        )
        await asyncio.gather(
            *(user_engine.liquidate_user_profit(user.id) for user in users)
        )


async def sync_dividend_data_task():
    """同步分红数据."""
    sqlalchemy.dialects.registry.register(
        "dremio", "sqlalchemy_dremio.pyodbc", "DremioDialect_pyodbc"
    )
    engine = create_engine(
        f"dremio://{settings.DREMIO_UID}:{settings.DREMIO_PWD}@{settings.DREMIO_HOST}:{settings.DREMIO_PORT}/dremio"
    )
    user_cache = UserCache(state.user_redis_pool)
    position_cache = PositionCache(state.position_redis_pool)
    users = await user_cache.get_all_user()
    db = state.db_client.get_database(settings.db.name, codec_options=codec_option)
    dividend_records_repository = DividendRecordsRepository(db=db)
    statement_repository = StatementRepository(db=db)
    today_date = datetime.combine(datetime.today().date(), datetime.min.time())
    cash_sql = """SELECT * FROM zvt.dividend_detail WHERE code={code} AND dividend_date='{today_date}';"""
    stock_sql = """SELECT * FROM zvt.dividend_detail WHERE code={code} AND dividend_pay_date='{today_date}';"""
    for user in users:
        user_position_list = await position_cache.get_position_by_user_id(user.id)
        for user_position in user_position_list:
            cash_df = pd.read_sql(
                cash_sql.format(code=user_position.symbol, today_date=today_date),
                engine,
            )
            user_cache_include = position_cache_include = set()
            dividend_record = DividendRecordsInDB(
                user=user.id,
                symbol=user_position.symbol,
                exchange=user_position.exchange,
            )
            # 现金红利
            if not cash_df.empty:
                df_record = cash_df.to_dict("records")[-1]
                volume = 0
                statement_list = (
                    await statement_repository.get_statement_list_by_symbol(
                        user_id=user.id, symbol=user_position.symbol
                    )
                )
                for statement in statement_list:
                    if statement.deal_time <= df_record["record_date"].replace(
                        tzinfo=timezone.utc
                    ):
                        if statement.trade_category == TradeCategoryEnum.BUY:
                            volume += statement.volume
                        else:
                            volume -= statement.volume
                if volume <= 0:
                    continue
                if df_record.get("dividend_per_share_before_tax"):
                    dividend_cash = Decimal(
                        round(df_record["dividend_per_share_before_tax"], 2)
                    ) * Decimal(volume)
                    dividend_record.cash = PyDecimal(dividend_cash)
                    # 更新用户现金
                    user.cash = PyDecimal(user.cash.to_decimal() + dividend_cash)
                    user_cache_include.add("cash")
                    # 持仓成本 = 总花费 / 持仓数量
                    #         = (原总花费 - 现金红利) / 持仓数量
                    cost = (
                        Decimal(user_position.volume) * user_position.cost.to_decimal()
                        - dividend_cash
                    ) / Decimal(user_position.volume)
                    # 更新持仓成本
                    user_position.cost = PyDecimal(cost)
                    position_cache_include.add("cost")
            # 股票红利
            stock_df = pd.read_sql(
                stock_sql.format(code=user_position.symbol, today_date=today_date),
                engine,
            )
            if not stock_df.empty:
                df_record = cash_df.to_dict("records")[-1]
                volume = 0
                statement_list = (
                    await statement_repository.get_statement_list_by_symbol(
                        user_id=user.id, symbol=user_position.symbol
                    )
                )
                for statement in statement_list:
                    if statement.deal_time <= df_record["record_date"].replace(
                        tzinfo=timezone.utc
                    ):
                        if statement.trade_category == TradeCategoryEnum.BUY:
                            volume += statement.volume
                        else:
                            volume -= statement.volume
                if volume <= 0:
                    continue
                if df_record.get("share_bonus_per_share"):
                    dividend_volume = int(
                        round(df_record["dividend_per_share_before_tax"], 2) * volume
                    )
                    dividend_record.volume = dividend_volume
                    # 持仓成本 = 总花费 / 持仓数量
                    #         = 原总花费 / (持仓数量 + 股票红利)
                    cost = (
                        Decimal(user_position.volume)
                        * user_position.cost.to_decimal()
                        / (user_position.volume + dividend_volume)
                    )
                    user_position.cost = PyDecimal(cost)
                    position_cache_include.add("cost")
            await user_cache.update_user(user, include=user_cache_include)
            await position_cache.update_position(
                user_position, include=position_cache_include
            )
            await dividend_records_repository.create_dividend_records(dividend_record)
