import click
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid

from app import settings
from scripts.utils import coro


async def create_collection(db: AsyncIOMotorClient, collection_name: str):
    """创建表."""
    try:
        await db[settings.MONGO_DB].create_collection(collection_name)
    except CollectionInvalid as e:
        click.echo(e)
    else:
        click.echo(f"创建{collection_name}成功\n")


@click.command("initdb")
@coro
async def init_db():
    """初始化数据库."""
    if click.confirm("初始化数据库可能会导致原数据丢失，确认要继续吗？"):
        client = AsyncIOMotorClient(settings.db.url)
        await create_collection(client, settings.db.collections.user)
        await create_collection(client, settings.db.collections.order)
        await client[settings.MONGO_DB][settings.db.collections.order].create_index(
            "entrust_id"
        )
        await create_collection(client, settings.db.collections.position)
        await client[settings.MONGO_DB][settings.db.collections.position].create_index(
            "user"
        )
        await client[settings.MONGO_DB][settings.db.collections.position].create_index(
            "symbol"
        )
        await client[settings.MONGO_DB][settings.db.collections.position].create_index(
            "exchange"
        )
        await create_collection(client, settings.db.collections.user_assets_record)
        await create_collection(client, settings.db.collections.statement)
        click.echo("初始化数据库完成.")
    else:
        click.echo("初始化数据库失败，用户操作中止.")
