import json
from decimal import Decimal

import click
from bson import ObjectId
from hq2redis import HQ2Redis
from hq2redis.reader import get_security_price
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.models.domain.statement import Costs, StatementInDB
from app.models.enums import OrderStatusEnum, OrderTypeEnum
from app.models.schemas.users import UserInUpdate
from app.models.types import PyDecimal
from scripts.utils import coro


@click.command("sync_user_assets")
@coro
async def sync_user_assets():
    """根据持仓同步用户资产数据."""
    client = AsyncIOMotorClient(settings.db.url)
    database = client.get_database(settings.MONGO_DB)
    account_db_conn = database[settings.db.collections.user]
    position_db_conn = database[settings.db.collections.position]
    users = account_db_conn.find()
    quotes_api = HQ2Redis(
        redis_host=settings.redis_host,
        redis_port=settings.redis_port,
        redis_db=settings.redis.hq_db,
        jqdata_password=settings.jqdata_password,
        jqdata_user=settings.jqdata_user,
    )
    await quotes_api.startup()
    async_user_assets_log_file = "sync_user_assets_log.json"
    update_logs = []
    async for user in users:
        position_rows = position_db_conn.find({"user": ObjectId(user["_id"])})
        user_position = [position async for position in position_rows]
        if not user_position:
            continue
        market_value = 0
        for row in user_position:
            security = await get_security_price(f"{row['symbol']}.{row['exchange']}")
            market_value += security.current * Decimal(row["volume"])
        assets = PyDecimal(market_value + user["cash"].to_decimal())
        securities = PyDecimal(market_value)
        user_in_db = UserInUpdate(
            assets=assets, securities=securities, id=user["_id"], cash=user["cash"]
        )
        await account_db_conn.update_one(
            {"_id": user_in_db.id}, {"$set": user_in_db.dict(exclude={"id", "cash"})}
        )
        update_logs.append(
            {
                "user_id": str(user["_id"]),
                "raw_user_assets": str(user["assets"]),
                "new_user_assets": str(assets),
                "raw_user_securities": str(user["securities"]),
                "new_user_securities": str(securities),
            }
        )
    with open(async_user_assets_log_file, "w", encoding="utf-8") as f:
        json.dump(update_logs, f, ensure_ascii=False, indent=4)
    await quotes_api.shutdown()


@click.command("sync_statement")
@coro
async def sync_statement():
    """根据委托单同步交割单."""
    client = AsyncIOMotorClient(settings.db.url)
    database = client.get_database(settings.MONGO_DB)
    order_db_conn = database[settings.db.collections.order]
    statement_db_conn = database[settings.db.collections.statement]
    user_db_conn = database[settings.db.collections.user]
    orders = order_db_conn.find(
        {
            "status": OrderStatusEnum.ALL_FINISHED,
            "order_type": {"$nin": [OrderTypeEnum.CANCEL.value]},
        }
    )
    logger.info("开始同步交割单...")
    sync_statement_log_file = "sync_statement_log.json"
    update_logs = []
    async for order in orders:
        statement_exists = await statement_db_conn.find_one(
            {"entrust_id": order["entrust_id"]}
        )
        if not statement_exists:
            traded_volume = order["traded_volume"]
            sold_price = order["sold_price"]
            securities = Decimal(traded_volume) * sold_price.to_decimal()
            user = await user_db_conn.find_one({"_id": order["user"]})
            commission = securities * user["commission"].to_decimal()
            if order["order_type"] == "buy":
                costs = Costs(commission=commission, total=commission, tax="0")
                amount = -(costs.total.to_decimal() + securities)
            else:
                tax = securities * user["tax_rate"].to_decimal()
                costs = Costs(commission=commission, tax=tax, total=commission + tax)
                amount = costs.total.to_decimal() + securities
            statement = StatementInDB(
                symbol=order["symbol"],
                exchange=order["exchange"],
                entrust_id=order["entrust_id"],
                user=order["user"],
                trade_category=order["order_type"],
                volume=traded_volume,
                sold_price=sold_price,
                costs=costs,
                amount=amount,
                deal_time=order.get("deal_time") or order.get("order_date"),
            )
            row = await statement_db_conn.insert_one(statement.dict(exclude={"id"}))
            update_logs.append(
                {
                    "entrust_id": str(statement.entrust_id),
                    "inserted_id": str(row.inserted_id),
                }
            )
    with open(sync_statement_log_file, "w", encoding="utf-8") as f:
        json.dump(update_logs, f, ensure_ascii=False, indent=4)
    logger.info(
        f"同步交割单完成, 共同步{len(update_logs)}条交割单, 同步结果已写入{sync_statement_log_file}."
    )
