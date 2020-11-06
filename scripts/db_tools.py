import json
import asyncio
from decimal import Decimal
from functools import wraps
from datetime import datetime

import click
from bson import ObjectId
from hq2redis import HQ2Redis
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app import settings
from app.models.types import PyDecimal
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
from app.models.schemas.users import UserInUpdate
from app.models.domain.position import PositionInDB
from app.models.domain.user_assets_records import UserAssetsRecordInDB


async def create_collection(db: AsyncIOMotorClient, collection_name: str):
    """创建表"""
    try:
        await db[settings.db.name].create_collection(collection_name)
    except CollectionInvalid as e:
        click.echo(e)
    else:
        click.echo(f"创建{collection_name}成功\n")


@click.group()
def cli():
    pass


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@cli.command()
@coro
async def initdb():
    """初始化数据库"""
    if click.confirm("初始化数据库可能会导致原数据丢失，确认要继续吗？"):
        client = AsyncIOMotorClient(settings.db.url)
        await create_collection(client, settings.db.collections.user)
        await create_collection(client, settings.db.collections.order)
        await client[settings.db.name][settings.db.collections.order].create_index("entrust_id")
        await create_collection(client, settings.db.collections.position)
        await client[settings.db.name][settings.db.collections.position].create_index("user")
        await client[settings.db.name][settings.db.collections.position].create_index("symbol")
        await client[settings.db.name][settings.db.collections.position].create_index("exchange")
        await create_collection(client, settings.db.collections.user_assets_record)
        click.echo("初始化数据库完成.")
    else:
        click.echo("初始化数据库失败，用户操作中止.")


@cli.command(name="insert_v1_data")
@coro
async def insert_v1_data():
    client = AsyncIOMotorClient(settings.db.url)
    v2_database = client.get_database(settings.db.name)

    db_tag_mapping = {1: "用户", 2: "用户资产时点数据", 3: "持仓", 4: "订单"}
    db_tag_num = click.prompt(
        f"请输入要插入的V1数据类型序号\n{db_tag_mapping}\n(请先插入用户数据)",
        type=int
    )
    if db_tag_num not in db_tag_mapping.keys():
        click.echo("请输入正确的序号.")
        return None
    db_tag = db_tag_mapping[db_tag_num]

    v1_db_name = click.prompt(f"请输入要插入的{db_tag}数据库名称", type=str)
    v1_database = client.get_database(v1_db_name)
    v1_collection_names = await v1_database.list_collection_names()

    # 写入文件的路径
    user_mapping_file_path = "./user_mapping.json"
    order_mapping_file_path = "./order_mapping.json"
    log_file_path = f"insert_log_{db_tag}_{datetime.today()}.json"

    # 数据
    insert_logs = []
    order_mapping = []
    if db_tag_num == 1:
        user_mapping = {}
    else:
        try:
            with open(user_mapping_file_path) as f:
                user_mapping = json.load(f)
        except FileNotFoundError:
            raise ValueError("请先插入用户数据.")

    # 找到V1数据的数量
    find_count = 0

    # 插入数据前先判断是否能找到该用户
    v2_account_db_conn = v2_database[settings.db.collections.user]

    if db_tag_num == 1:
        # 用户表
        click.echo("插入用户到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_account_conn = v1_database[v1_conn_name]
            v1_user = await v1_account_conn.find_one()
            insert_info = {
                "v1_row_id": str(v1_user.get("_id"))
            }
            try:
                user = UserInDB(
                    assets=str(v1_user.get("assets")),
                    cash=str(v1_user.get("available")),
                    securities=str(v1_user.get("market_value")),
                    capital=str(v1_user.get("capital")),
                    commission=str(v1_user.get("cost")),
                    tax_rate=str(v1_user.get("tax")),
                    slippage=str(v1_user.get("slippoint")),
                    desc=v1_user.get("account_info")
                )
                row = await v2_account_db_conn.insert_one(user.dict(exclude={"id"}))
            except Exception as e:
                insert_info["status"] = "Error"
                insert_info["error_msg"] = str(e)
            else:
                insert_info["status"] = "Success"
                insert_info["inserted_id"] = str(row.inserted_id)
                user_mapping[v1_user["account_id"]] = {
                    "v1_user_id": v1_user["account_id"],
                    "v2_user_id": str(row.inserted_id),
                }
            finally:
                insert_logs.append(insert_info)
                find_count += 1

    elif db_tag_num == 2:
        # 用户资产时点数据表
        v2_account_record_db_conn = v2_database[settings.db.collections.user_assets_record]
        click.echo("插入用户资产时点数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_account_record_conn = v1_database[v1_conn_name]
            v1_user_records = v1_account_record_conn.find()
            async for v1_user_record in v1_user_records:
                insert_info = {
                    "v1_row_id": str(v1_user_record.get("_id"))
                }
                mapping_dict = user_mapping.get(v1_conn_name)
                if not mapping_dict:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "该用户未写入."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                v2_user_id = ObjectId(mapping_dict["v2_user_id"])
                v2_user = await v2_account_db_conn.find_one({"_id": v2_user_id})
                if not v2_user:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "未找到该用户."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                try:
                    check_date = datetime.strptime(str(v1_user_record.get("check_date")), "%Y%m%d")
                    user_record = UserAssetsRecordInDB(
                        user=v2_user_id,
                        assets=str(v1_user_record.get("assets", 0)),
                        cash=str(v1_user_record.get("available", 0)),
                        securities=str(v1_user_record.get("market_value", 0)),
                        date=check_date,
                        check_time=check_date
                    )
                    row = await v2_account_record_db_conn.insert_one(user_record.dict(exclude={"id"}))
                except Exception as e:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = str(e)
                else:
                    insert_info["status"] = "Success"
                    insert_info["inserted_id"] = str(row.inserted_id)
                finally:
                    insert_logs.append(insert_info)
                    find_count += 1

    elif db_tag_num == 3:
        # 持仓表
        v2_position_db_conn = v2_database[settings.db.collections.position]
        click.echo("插入用户持仓数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_position_conn = v1_database[v1_conn_name]
            v1_position_list = v1_position_conn.find()
            async for v1_position in v1_position_list:
                insert_info = {
                    "v1_row_id": str(v1_position.get("_id"))
                }
                mapping_dict = user_mapping.get(v1_conn_name)
                if not mapping_dict:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "该用户未写入."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                v2_user_id = ObjectId(mapping_dict["v2_user_id"])
                v2_user = await v2_account_db_conn.find_one({"_id": v2_user_id})
                if not v2_user:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "未找到该用户."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                try:
                    first_buy_date_str = v1_position.get("first_buy_date")
                    first_buy_date = datetime.strptime(first_buy_date_str, "%Y%m%d") if first_buy_date_str else None
                    last_sell_date_str = v1_position.get("last_sell_date")
                    last_sell_date = datetime.strptime(last_sell_date_str, "%Y%m%d") if first_buy_date_str else None
                    position_in_db = PositionInDB(
                        symbol=v1_position.get("code"),
                        exchange=v1_position.get("exchange"),
                        user=v2_user_id,
                        first_buy_date=first_buy_date,
                        last_sell_date=last_sell_date,
                        volume=v1_position.get("volume"),
                        available_volume=v1_position.get("available"),
                        cost=str(v1_position.get("buy_price")),
                        current_price=str(v1_position.get("now_price")),
                        profit=str(v1_position.get("profit")),
                    )
                    row = await v2_position_db_conn.insert_one(position_in_db.dict(exclude={"id"}))
                except Exception as e:
                    insert_info["conn_name"] = v1_conn_name
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = str(e)
                else:
                    insert_info["status"] = "Success"
                    insert_info["inserted_id"] = str(row.inserted_id)
                finally:
                    insert_logs.append(insert_info)
                    find_count += 1

    elif db_tag_num == 4:
        # 订单表
        order_db_v2_conn = v2_database[settings.db.collections.order]
        click.echo("插入订单数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_order_conn = v1_database[v1_conn_name]
            v1_orders = v1_order_conn.find()
            async for v1_order in v1_orders:
                insert_info = {
                    "v1_row_id": str(v1_order.get("_id"))
                }
                mapping_dict = user_mapping.get(v1_conn_name)
                if not mapping_dict:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "该用户未写入."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                v2_user_id = ObjectId(mapping_dict["v2_user_id"])
                v2_user = await v2_account_db_conn.find_one({"_id": v2_user_id})
                if not v2_user:
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = "未找到该用户."
                    insert_logs.append(insert_info)
                    find_count += 1
                    continue
                try:
                    v1_user_id = v1_order.get("account_id")
                    user_id = ObjectId(user_mapping[v1_user_id]["v2_user_id"])
                    user_v2 = await v2_account_db_conn.find_one({"_id": user_id})
                    assert user_v2
                    order_type = v1_order.get("order_type")
                    if order_type == "liquidation":
                        continue
                    price_type_mapping = {
                        "限价": "limit",
                        "市价": "market",
                    }
                    trade_type_str = v1_order.get("trade_type")
                    trade_type = trade_type_str.upper() if trade_type_str else "T1"

                    trade_price_str = v1_order.get("order_price")
                    trade_price = str(trade_price_str) if trade_price_str else None

                    trade_status_str = v1_order.get("status")
                    trade_status = "已拒单" if trade_status_str == "拒单" else trade_status_str

                    order_date_str = v1_order.get("order_date")
                    if len(order_date_str) > 8:
                        order_date = datetime.strptime(order_date_str, "%Y-%m-%d")
                    else:
                        order_date = datetime.strptime(order_date_str, "%Y%m%d")

                    order_in_db = OrderInDB(
                        symbol=v1_order.get("code"),
                        exchange=v1_order.get("exchange"),
                        user=user_id,
                        entrust_id=ObjectId(),
                        order_type=order_type,
                        price_type=price_type_mapping[v1_order.get("price_type")],
                        trade_type=trade_type,
                        volume=v1_order.get("volume"),
                        price=str(v1_order.get("order_price")),
                        sold_price=trade_price,
                        traded_volume=v1_order.get("traded", 0),
                        status=trade_status,
                        order_date=order_date,
                        position_change=str(v1_order.get("pos_change"))
                    )
                    row = await order_db_v2_conn.insert_one(order_in_db.dict(exclude={"id"}))
                except Exception as e:
                    insert_info["conn_name"] = v1_conn_name
                    insert_info["status"] = "Error"
                    insert_info["error_msg"] = str(e)
                else:
                    insert_info["status"] = "Success"
                    insert_info["inserted_id"] = str(row.inserted_id)
                    order_mapping.append({
                        "v1_order_id": v1_order.get("order_id"),
                        "v2_order_id": str(order_in_db.entrust_id)
                    })
                finally:
                    insert_logs.append(insert_info)
                    find_count += 1

    client.close()
    success_count = len([insert_log for insert_log in insert_logs if insert_log.get("status") == "Success"])
    click.echo(f"共找到{find_count}条{db_tag}数据，成功插入{success_count}条.")
    with open(log_file_path, "w", encoding="utf-8") as f:
        json.dump(insert_logs, f, ensure_ascii=False, indent=4)
    if db_tag_num == 1:
        with open(user_mapping_file_path, "w", encoding="utf-8") as f:
            json.dump(user_mapping, f, ensure_ascii=False, indent=4)
    if db_tag_num == 4:
        with open(order_mapping_file_path, "w", encoding="utf-8") as f:
            json.dump(order_mapping, f, ensure_ascii=False, indent=4)
    click.echo(f"插入结果已写入`{log_file_path}`中.")


@cli.command(name="sync_user_assets")
@coro
async def sync_user_assets():
    client = AsyncIOMotorClient(settings.db.url)
    database = client.get_database(settings.db.name)
    account_db_conn = database[settings.db.collections.user]
    position_db_conn = database[settings.db.collections.position]
    users = account_db_conn.find()
    quotes_api = HQ2Redis(
        redis_host=settings.redis.host,
        redis_port=settings.redis.port,
        redis_db=settings.redis.hq_db,
        jq_data_password=settings.jqdata_password,
        jq_data_user=settings.jqdata_user,
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
            quotes = await quotes_api.get_stock_ticks(f"{row['symbol']}.{row['exchange']}")
            market_value += quotes.current * Decimal(row["volume"])
        assets = PyDecimal(market_value + user["cash"].to_decimal())
        securities = PyDecimal(market_value)
        user_in_db = UserInUpdate(assets=assets, securities=securities, id=user["_id"], cash=user["cash"])
        await account_db_conn.update_one({"_id": user_in_db.id}, {"$set": user_in_db.dict(exclude={"id", "cash"})})
        update_logs.append({
            "user_id": str(user["_id"]),
            "raw_user_assets": str(user["assets"]),
            "new_user_assets": str(assets),
            "raw_user_securities": str(user["securities"]),
            "new_user_securities": str(securities)
        })
    with open(async_user_assets_log_file, "w", encoding="utf-8") as f:
        json.dump(update_logs, f, ensure_ascii=False, indent=4)
    await quotes_api.shutdown()

if __name__ == "__main__":
    cli()
