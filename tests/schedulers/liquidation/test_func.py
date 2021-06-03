import datetime
from copy import deepcopy
from decimal import Decimal

import pytest
from dividend_utils.enums import Exchange, FlowType
from dividend_utils.models import Flow

from app.models.schemas.position import PositionInCache
from app.models.schemas.users import UserInCache
from app.schedulers.liquidation.func import (
    dividend_flow2pt,
    liquidate_dividend_by_position,
    liquidate_dividend_task,
    update_position_by_flow,
    update_position_cost,
    update_user_by_flow,
)

pytestmark = pytest.mark.asyncio


user = UserInCache(
    id="60b6e5d4d6bbc0855f194f25",
    capital="1000000",
    assets="1000000",
    cash="1000000",
    available_cash="1000000",
    securities="0",
    commission="0",
    tax_rate="0",
)

position = PositionInCache(
    user="60b6e5d4d6bbc0855f194f25",
    volume=100,
    available_volume=100,
    cost="100",
    current_price="1100",
    profit="100000",
    symbol="600519",
    exchange="SH",
)


@pytest.mark.parametrize("stkeffect, fundeffect", [(100, 0), (0, 100)])
def test_dividend_flow2pt(stkeffect, fundeffect):
    flow = Flow(
        fund_id="60b6e5d4d6bbc0855f194f25",
        symbol="600519",
        exchange=Exchange.CNSESH,
        ttype=FlowType.DIVIDEND,
        tdate=datetime.date(2019, 1, 1),
        stkeffect=stkeffect,
        fundeffect=fundeffect,
    )
    rv = dividend_flow2pt(flow)
    assert rv.trade_category == "dividend"
    assert rv.amount.to_decimal() == Decimal(fundeffect)
    assert rv.volume == stkeffect


@pytest.mark.parametrize(
    "liq_date, excepted_len",
    [
        (datetime.date(2020, 6, 23), 1),
        (datetime.date(2020, 6, 24), 0),
        (datetime.date(2011, 6, 30), 2),
    ],
)
async def test_liquidate_dividend_by_position(liq_date, excepted_len):
    rv = await liquidate_dividend_by_position(position, liq_date)
    assert len(rv) == excepted_len


async def test_liquidate_dividend_task(initialized_app, mocker):
    def fake_user_cache(*args, **kwargs):
        class FakeUserCache:
            def __init__(self, *args, **kwargs):
                ...

            async def get_all_user(*args, **kwargs):
                return [user]

        return FakeUserCache

    def fake_position_cache(*args, **kwargs):
        class FakePositionCache:
            def __init__(self, *args, **kwargs):
                ...

            async def get_position_by_user_id(*args, **kwargs):
                return [position]

        return FakePositionCache

    user_cache_mocker = mocker.patch("app.schedulers.liquidation.func.UserCache")
    user_cache_mocker.side_effect = fake_user_cache
    position_cache_mocker = mocker.patch(
        "app.schedulers.liquidation.func.PositionCache"
    )
    position_cache_mocker.side_effect = fake_position_cache
    await liquidate_dividend_task()


@pytest.mark.parametrize(
    "stkeffect, fundeffect, excepted_cash",
    [(100, 0, Decimal(0)), (0, 100, Decimal(100))],
)
async def test_update_user_by_flow(stkeffect, fundeffect, excepted_cash):
    flow = Flow(
        fund_id="60b6e5d4d6bbc0855f194f25",
        symbol="600519",
        exchange=Exchange.CNSESH,
        ttype=FlowType.DIVIDEND,
        tdate=datetime.date(2019, 1, 1),
        stkeffect=stkeffect,
        fundeffect=fundeffect,
    )
    statement = dividend_flow2pt(flow)
    new_user = deepcopy(user)
    rv = await update_user_by_flow(new_user, statement)
    assert excepted_cash == rv.cash.to_decimal() - user.cash.to_decimal()
    assert (
        excepted_cash
        == rv.available_cash.to_decimal() - user.available_cash.to_decimal()
    )
    assert excepted_cash == rv.assets.to_decimal() - user.assets.to_decimal()


@pytest.mark.parametrize(
    "stkeffect, fundeffect, pay_date",
    [(100, 0, datetime.date(2015, 7, 17)), (0, 100, datetime.date(2020, 6, 24))],
)
async def test_update_position_by_flow(stkeffect, fundeffect, pay_date):
    flow = Flow(
        fund_id="60b6e5d4d6bbc0855f194f25",
        symbol="600519",
        exchange=Exchange.CNSESH,
        ttype=FlowType.DIVIDEND,
        tdate=pay_date,
        stkeffect=stkeffect,
        fundeffect=fundeffect,
    )
    statement = dividend_flow2pt(flow)
    new_position = deepcopy(position)
    rv = await update_position_by_flow(new_position, statement)
    if stkeffect != 0:
        assert rv.volume == position.volume + stkeffect
        assert rv.cost.to_decimal() == Decimal("86.933")
        assert rv.profit.to_decimal() == Decimal("202613.400")
    else:
        assert rv.volume == position.volume
        assert rv.cost.to_decimal() == Decimal("82.975")
        assert rv.profit.to_decimal() == Decimal("101702.500")


@pytest.mark.parametrize(
    "tax, cost", [(Decimal(-100), Decimal("101")), (Decimal(-10), Decimal("100.1"))]
)
async def test_update_position_cost(tax, cost):
    new_position = deepcopy(position)
    rv = await update_position_cost(new_position, tax)
    assert rv.cost.to_decimal() == cost
