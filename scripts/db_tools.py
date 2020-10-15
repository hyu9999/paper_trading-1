import json
import asyncio
from functools import wraps
from datetime import datetime

import click
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app import settings
from app.models.domain.users import UserInDB
from app.models.domain.orders import OrderInDB
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

    # 成功插入到V2数据库中的ID列表
    insert_logs = []
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
            insert_status = {
                "_id": str(v1_user.get("_id"))
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
                user_dict = user.dict(exclude={"id"})
                user_dict["_id"] = ObjectId(v1_user.get("account_id"))
                row = await v2_account_db_conn.insert_one(user_dict)
            except Exception as e:
                insert_status["status"] = "Error"
                insert_status["error_msg"] = str(e)
            else:
                insert_status["status"] = "Success"
                insert_status["inserted_id"] = str(row.inserted_id)
            finally:
                insert_logs.append(insert_status)
                find_count += 1

    elif db_tag_num == 2:
        # 用户持仓时点数据表
        v2_account_record_db_conn = v2_database[settings.db.collections.user_assets_record]
        click.echo("插入用户持仓时点数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_account_record_conn = v1_database[v1_conn_name]
            v1_user_record = await v1_account_record_conn.find_one()
            insert_status = {
                "_id": str(v1_user_record.get("_id"))
            }
            try:
                user_id = ObjectId(v1_user_record.get("account_id"))
                user_v2 = await v2_account_db_conn.find_one({"_id": user_id})
                assert user_v2
                check_date = datetime.strptime(v1_user_record.get("check_date"), "%Y%m%d")
                user_record = UserAssetsRecordInDB(
                    user=user_id,
                    assets=str(v1_user_record.get("assets", 0)),
                    cash=str(v1_user_record.get("available", 0)),
                    securities=str(v1_user_record.get("market_value", 0)),
                    date=check_date,
                    check_time=check_date
                )
                row = await v2_account_record_db_conn.insert_one(user_record)
            except Exception as e:
                insert_status["status"] = "Error"
                insert_status["error_msg"] = str(e)
            else:
                insert_status["status"] = "Success"
                insert_status["inserted_id"] = str(row.inserted_id)
            finally:
                insert_logs.append(insert_status)
                find_count += 1

    elif db_tag_num == 3:
        # 持仓表
        v2_position_db_conn = v2_database[settings.db.collections.position]
        click.echo("插入用户持仓数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_position_conn = v1_database[v1_conn_name]
            v1_position = await v1_position_conn.find_one()
            insert_status = {
                "_id": str(v1_position.get("_id"))
            }
            try:
                user_id = ObjectId(v1_position.get("account_id"))
                user_v2 = await v2_account_db_conn.find_one({"_id": user_id})
                assert user_v2
                first_buy_date = datetime.strptime(v1_position.get("buy_price"), "%Y%m%d")
                position_in_db = PositionInDB(
                    symbol=v1_position.get("code"),
                    exchange=v1_position.get("exchange"),
                    user=user_id,
                    first_buy_date=first_buy_date,
                    volume=str(v1_position.get("volume")),
                    available_volume=str(v1_position.get("available")),
                    current_price=str(v1_position.get("now_price")),
                    profit=str(v1_position.get("profit")),
                )
                row = await v2_position_db_conn.insert_one(position_in_db)
            except Exception as e:
                insert_status["status"] = "Error"
                insert_status["error_msg"] = str(e)
            else:
                insert_status["status"] = "Success"
                insert_status["inserted_id"] = str(row.inserted_id)
            finally:
                insert_logs.append(insert_status)
                find_count += 1

    elif db_tag_num == 4:
        # 订单表
        order_db_v2_conn = v2_database[settings.db.collections.order]
        click.echo("插入订单数据到V2数据库中...")
        for v1_conn_name in v1_collection_names:
            v1_order_conn = v1_database[v1_conn_name]
            v1_order = await v1_order_conn.find_one()
            insert_status = {
                "_id": str(v1_order.get("_id"))
            }
            try:
                user_id = ObjectId(v1_order.get("account_id"))
                user_v2 = await v2_account_db_conn.find_one({"_id": user_id})
                assert user_v2
                order_type = v1_order.get("order_type")
                if order_type == "liquidation":
                    continue
                order_in_db = OrderInDB(
                    symbol=v1_order.get("code"),
                    exchange=v1_order.get("exchange"),
                    user=user_id,
                    entrust_id=v1_order.get("order_id"),
                    order_type=order_type,
                    price_type=v1_order.get("price_type"),
                    trade_type=v1_order.get("trade_type").upper(),
                    volume=str(v1_order.get("volume")),
                    price=str(v1_order.get("price")),
                    sold_price=str(v1_order.get("trade_price")),
                    traded_volume=str(v1_order.get("traded")),
                    status=str(v1_order.get("status")),
                    order_date=datetime.strptime(v1_order.get("order_date"), "%Y%m%d")
                )
                row = await order_db_v2_conn.insert_one(order_in_db)
            except Exception as e:
                insert_status["status"] = "Error"
                insert_status["error_msg"] = str(e)
            else:
                insert_status["status"] = "Success"
                insert_status["inserted_id"] = str(row.inserted_id)
            finally:
                insert_logs.append(insert_status)
                find_count += 1

    client.close()
    success_count = len([insert_log for insert_log in insert_logs if insert_log.get("status") == "Success"])
    click.echo(f"共找到{find_count}条{db_tag}数据，成功插入{success_count}条.")
    file_name = f"insert_log_{db_tag}_{datetime.today()}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(insert_logs, f, ensure_ascii=False, indent=4)
    click.echo(f"插入结果已写入{file_name}中.")

if __name__ == "__main__":
    cli()
