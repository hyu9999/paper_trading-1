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
    db_name_v1 = click.prompt("请输入V1版本Mongo数据库名称", type=str)
    database_v1 = client.get_database(db_name_v1)
    database_v2 = client.get_database(settings.db.name)

    db_tag_mapping = {1: "Account", 2: "AccountRecord", 3: "Position", 4: "Order"}
    db_tag_num = click.prompt(
        f"请输入要插入的连接名称序号{db_tag_mapping}",
        type=int
    )
    if db_tag_num not in db_tag_mapping.keys():
        click.echo("请输入正确的序号.")
        return None
    db_tag = db_tag_mapping[db_tag_num]
    # 成功插入到V2数据库中的ID列表
    inserted_id_list = []
    # 找到V1数据的数量
    find_count = 0

    account_record_db_v2_conn = database_v2[settings.db.collections.user_assets_record]

    if db_tag == "Account":
        # 用户表
        account_conn_name = click.prompt("请输入V1版本Account表名", type=str)
        account_db_v1_conn = database_v1[account_conn_name]
        account_db_v2_conn = database_v2[settings.db.collections.user]
        users_v1 = account_db_v1_conn.find()
        click.echo("插入用户到V2数据库中...")
        async for user_v1 in users_v1:
            try:
                user = UserInDB(
                    assets=str(user_v1.get("assets")),
                    cash=str(user_v1.get("available")),
                    securities=str(user_v1.get("market_value")),
                    capital=str(user_v1.get("capital")),
                    commission=str(user_v1.get("cost")),
                    tax_rate=str(user_v1.get("tax")),
                    slippage=str(user_v1.get("slippoint")),
                    desc=user_v1.get("account_info")
                )
                user_dict = user.dict(exclude={"id"})
                user_dict["_id"] = ObjectId(user_v1.get("account_id"))
                row = await account_db_v2_conn.insert_one(user_dict)
                inserted_id_list.append(row.inserted_id)
            except Exception:
                continue
            find_count += 1

    elif db_tag == "AccountRecord":
        # 用户持仓时点数据表
        account_record_conn_name = click.prompt("请输入V1版本AccountRecord表名", type=str)
        account_record_db_v1_conn = database_v1[account_record_conn_name]
        user_records_v1 = account_record_db_v1_conn.find()
        click.echo("插入用户持仓时点数据到V2数据库中...")
        async for user_record_v1 in user_records_v1:
            try:
                user_id = ObjectId(user_record_v1.get("account_id"))
                user_v2 = account_record_db_v2_conn.find_one({"_id": user_id})
                assert user_v2
                check_date = datetime.strptime(user_record_v1.get("check_date"), "%Y%m%d")
                user_record = UserAssetsRecordInDB(
                    user=user_id,
                    assets=str(user_record_v1.get("assets", 0)),
                    cash=str(user_record_v1.get("available", 0)),
                    securities=str(user_record_v1.get("market_value", 0)),
                    date=check_date,
                    check_time=check_date
                )
                row = await account_record_db_v2_conn.insert_one(user_record)
                inserted_id_list.append(row.inserted_id)
            except Exception:
                continue
            find_count += 1

    elif db_tag == "Position":
        # 持仓表
        position_conn_name = click.prompt("请输入V1版本Position表名", type=str)
        position_db_v1_conn = database_v1[position_conn_name]
        position_db_v2_conn = database_v2[settings.db.collections.position]
        position_list_v1 = position_db_v1_conn.find()
        click.echo("插入用户持仓数据到V2数据库中...")
        async for position_v1 in position_list_v1:
            try:
                user_id = ObjectId(position_v1.get("account_id"))
                user_v2 = account_record_db_v2_conn.find_one({"_id": user_id})
                assert user_v2
                first_buy_date = datetime.strptime(position_v1.get("buy_price"), "%Y%m%d")
                position_in_db = PositionInDB(
                    symbol=position_v1.get("code"),
                    exchange=position_v1.get("exchange"),
                    user=user_id,
                    first_buy_date=first_buy_date,
                    volume=str(position_v1.get("volume")),
                    available_volume=str(position_v1.get("available")),
                    current_price=str(position_v1.get("now_price")),
                    profit=str(position_v1.get("profit")),
                )
                row = await position_db_v2_conn.insert_one(position_in_db)
                inserted_id_list.append(row.inserted_id)
            except Exception:
                continue
            find_count += 1

    elif db_tag == "Order":
        # 订单表
        order_conn_name = click.prompt("请输入V1版本Order表名", type=str)
        order_db_v1_conn = database_v1[order_conn_name]
        order_db_v2_conn = database_v2[settings.db.collections.order]
        orders_v1 = order_db_v1_conn.find()
        click.echo("插入订单数据到V2数据库中...")
        async for order_v1 in orders_v1:
            try:
                user_id = ObjectId(order_v1.get("account_id"))
                user_v2 = account_record_db_v2_conn.find_one({"_id": user_id})
                assert user_v2
                order_type = orders_v1.get("order_type")
                if order_type == "liquidation":
                    continue
                order_in_db = OrderInDB(
                    symbol=order_v1.get("code"),
                    exchange=order_v1.get("exchange"),
                    user=user_id,
                    entrust_id=order_v1.get("order_id"),
                    order_type=order_type,
                    price_type=order_v1.get("price_type"),
                    trade_type=order_v1.get("trade_type").upper(),
                    volume=str(order_v1.get("volume")),
                    price=str(orders_v1.get("price")),
                    sold_price=str(order_v1.get("trade_price")),
                    traded_volume=str(order_v1.get("traded")),
                    status=str(order_v1.get("status")),
                    order_date=datetime.strptime(order_v1.get("order_date"), "%Y%m%d")
                )
                row = await order_db_v2_conn.insert_one(order_in_db)
                inserted_id_list.append(row.inserted_id)
            except Exception:
                continue
            find_count += 1

    click.echo(f"共找到{find_count}条{db_tag}数据，成功插入{len(inserted_id_list)}条.")
    file_name = f"insert_log_{db_tag}_{datetime.today()}.txt"
    with open(file_name, "w") as f:
        for insert_id in inserted_id_list:
            f.write(f"{insert_id}\n")
    click.echo(f"插入结果已写入{file_name}中.")

if __name__ == "__main__":
    cli()
