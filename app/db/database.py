from motor.motor_asyncio import AsyncIOMotorClient


class DataBase:
    client: AsyncIOMotorClient = None


_db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return _db.client
