import datetime
from decimal import Decimal
from typing import List

from dividend_utils.dividend import get_xdr_price
from dividend_utils.liquidator import liquidate_dividend, liquidate_dividend_tax
from dividend_utils.models import Flow, Position

from app import state
from app.db.cache.position import PositionCache
from app.db.cache.user import UserCache
from app.db.repositories.statement import StatementRepository
from app.exceptions.db import EntityDoesNotExist
from app.models.base import get_utc_now
from app.models.domain.statement import Costs, StatementInDB
from app.models.enums import TradeCategoryEnum
from app.models.schemas.position import PositionInCache
from app.models.schemas.users import UserInCache
from app.models.types import PyDecimal, PyObjectId

MARKET_MAPPING = {"CNSESH": "SH", "CNSESZ": "SZ"}
MARKET_MAPPING_REVERSE = {"SH": "CNSESH", "SZ": "CNSESZ"}
no_cost = Costs(total="0", commission="0", tax="0")


def dividend_flow2pt(flow: Flow) -> StatementInDB:
    return StatementInDB(
        symbol=flow.symbol,
        exchange=MARKET_MAPPING[flow.exchange],
        user=PyObjectId(flow.fund_id),
        trade_category="dividend",
        volume=flow.stkeffect,
        amount=flow.fundeffect,
        costs=no_cost,
        deal_time=datetime.datetime.combine(flow.tdate, datetime.datetime.min.time()),
        entrust_id=None,
        sold_price="0",
    )


async def liquidate_dividend_by_position(
    position: PositionInCache, liq_date: datetime.date
) -> List[StatementInDB]:
    from zvt.api import DividendDetail

    dividend_detail = DividendDetail.query_data(
        filters=[DividendDetail.code == position.symbol]
    )
    position_dict = position.dict()
    position_dict["fund_id"] = str(position.user)
    position_dict["exchange"] = MARKET_MAPPING_REVERSE[position.exchange]
    dividend_flow_list = liquidate_dividend(
        dividend_detail, Position(**position_dict), liq_date
    )
    return [dividend_flow2pt(dividend_flow) for dividend_flow in dividend_flow_list]


async def liquidate_dividend_task():
    """清算分红."""
    user_cache = UserCache(state.user_redis_pool)
    position_cache = PositionCache(state.position_redis_pool)
    statement_repo = StatementRepository(state.db)

    users = await user_cache.get_all_user()
    liq_date = datetime.date.today()

    for user in users:
        position_list = await position_cache.get_position_by_user_id(user_id=user.id)
        for position in position_list:
            statement_list = await liquidate_dividend_by_position(position, liq_date)
            for statement in statement_list:
                await statement_repo.create_statement(statement)


def ptflow2dividend(flow: StatementInDB) -> Flow:
    """pt流水格式转换为dividend流水格式."""
    return Flow(
        fund_id=str(flow.user),
        symbol=flow.symbol,
        exchange=MARKET_MAPPING_REVERSE[flow.exchange],
        ttype=flow.deal_time.date(),
        stkeffect=flow.volume,
        fundeffect=flow.amount.to_decimal(),
        ts=flow.deal_time.timestamp(),
    )


def dividendflow2pt(flow: Flow) -> StatementInDB:
    """dividend流水格式转换为pt流水格式."""
    return StatementInDB(
        symbol=flow.symbol,
        exchange=MARKET_MAPPING[flow.exchange],
        user=PyObjectId(flow.fund_id),
        trade_category="tax",
        volume=flow.stkeffect,
        solod_price="0",
        amount=flow.fundeffect,
        costs=no_cost,
        deal_time=get_utc_now(),
    )


async def liquidate_dividend_tax_task():
    """清算红利税."""
    from zvt.api import DividendDetail

    statement_repo = StatementRepository(state.db)
    user_cache = UserCache(state.user_redis_pool)
    position_cache = PositionCache(state.position_redis_pool)

    order_list = await statement_repo.get_statement_list(
        start_date=get_utc_now().date(),
        end_date=get_utc_now().date(),
        trade_category=[TradeCategoryEnum.SELL],
    )
    for order in order_list:
        dividend_detail = DividendDetail.query_data(
            filters=[DividendDetail.code == order.symbol]
        )
        flow_list = await statement_repo.get_statement_list(
            trade_category=[TradeCategoryEnum.SELL, TradeCategoryEnum.BUY],
            symbol=order.symbol,
        )
        tax_flow = liquidate_dividend_tax(
            dividend_detail,
            ptflow2dividend(order),
            [ptflow2dividend(flow) for flow in flow_list],
        )
        if tax_flow:
            statement = dividendflow2pt(tax_flow)
            await statement_repo.create_statement(statement)
            user = await user_cache.get_user_by_id(statement.user)
            new_user = await update_user_by_flow(user, statement)
            await user_cache.update_user(new_user)
            try:
                position = await position_cache.get_position(
                    user.id, symbol=statement.symbol, exchange=statement.exchange
                )
            except EntityDoesNotExist:
                ...
            else:
                new_position = await update_position_cost(
                    position, statement.amount.to_decimal()
                )
                await position_cache.update_position(new_position)


async def update_user_by_flow(user: UserInCache, flow: StatementInDB) -> UserInCache:
    """通过分红流水更新账户."""
    user.cash = PyDecimal(user.cash.to_decimal() + flow.amount.to_decimal())
    user.available_cash = user.cash
    user.assets = PyDecimal(user.assets.to_decimal() + flow.amount.to_decimal())
    return user


async def update_position_by_flow(
    position: PositionInCache, flow: StatementInDB
) -> PositionInCache:
    """通过分红流水更新持仓."""
    from zvt.api import DividendDetail

    position.volume += flow.volume
    position.available_volume = position.volume
    # 更新成本价
    dividend_detail = DividendDetail.query_data(
        filters=[
            DividendDetail.code == position.symbol,
            DividendDetail.dividend_pay_date == flow.deal_time.date(),
        ]
    )
    # 获取除权除息后的价格
    xdr_cost = get_xdr_price(dividend_detail, float(position.cost.to_decimal()))
    position.cost = PyDecimal(str(xdr_cost))
    # 持仓利润 = (现价 - 成本价) * 持仓数量
    profit = (
        position.current_price.to_decimal() - position.cost.to_decimal()
    ) * Decimal(position.volume)
    position.profit = PyDecimal(profit)
    return position


async def update_position_cost(position: PositionInCache, tax: Decimal):
    """更新持仓成本."""
    tax_cost = abs(tax) / position.volume
    cost = position.cost.to_decimal() + tax_cost
    position.cost = PyDecimal(cost)
    return position


async def liquidate_dividend_flow_task():
    """清算分红流水."""
    user_cache = UserCache(state.user_redis_pool)
    position_cache = PositionCache(state.position_redis_pool)
    statement_repo = StatementRepository(state.db)

    dividend_flow_list = await statement_repo.get_statement_list(
        start_date=get_utc_now().date(),
        end_date=get_utc_now().date(),
        trade_category=[TradeCategoryEnum.DIVIDEND],
    )
    for flow in dividend_flow_list:
        user = await user_cache.get_user_by_id(flow.user)
        position = await position_cache.get_position(
            flow.user, flow.symbol, flow.exchange
        )
        new_user = await update_user_by_flow(user, flow)
        new_position = await update_position_by_flow(position, flow)
        await user_cache.update_user(new_user)
        await position_cache.update_position(new_position)
