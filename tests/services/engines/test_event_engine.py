import pytest

from app.services.engines.event_engine import EventEngine

pytestmark = pytest.mark.asyncio


async def test_event_engine_can_run():
    event_engine = EventEngine()
    await event_engine.startup()
    await event_engine.shutdown()
