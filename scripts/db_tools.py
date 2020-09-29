import logging
import asyncio
from functools import wraps

import click
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app import settings


async def create_collection(db: AsyncIOMotorClient, collection_name: str):
    """创建表"""
    try:
        await db[settings.db.name].create_collection(collection_name)
    except CollectionInvalid as e:
        logging.info(e)
    else:
        logging.info(f"创建{collection_name}成功\n")


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
        click.echo("初始化数据库完成.")
    else:
        click.echo("初始化数据库失败，用户操作中止.")


if __name__ == "__main__":
    cli()
