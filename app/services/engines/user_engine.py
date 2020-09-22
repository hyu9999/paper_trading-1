from motor.motor_asyncio import AsyncIOMotorClient

from app import settings
from app.services.engines.event_constants import USER_UPDATE_EVENT
from app.services.engines.event_engine import EventEngine, Event
from app.db.repositories.user import UserRepository


class UserEngine:
    def __init__(self, event_engine: EventEngine, db: AsyncIOMotorClient) -> None:
        self.event_engine = event_engine
        self.user_repo = UserRepository(db[settings.db.name])

    async def startup(self):
        await self.register_event()

    async def shutdown(self):
        pass

    async def register_event(self) -> None:
        await self.event_engine.register(USER_UPDATE_EVENT, self.process_update_user)

    def process_update_user(self, event: Event) -> None:
        user = event.data
        # await self.user_repo.update_user_cash_by_id(user.id, user.cash)
