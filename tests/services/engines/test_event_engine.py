import pytest

# from app.services.engines.event_engine import EventEngine, Event

pytestmark = pytest.mark.asyncio


def process_foo(event):
    assert event.payload == "foo"


def process_bar(event):
    assert event.payload != "foo"


# @pytest.mark.parametrize(
#     "event_type, event_payload, event_process",
#     (("foo_event", "foo", process_foo), ("bar_event", "bar", process_bar)),
# )
# async def test_event_engine_can_run(event_type, event_data, event_process):
#     event_engine = EventEngine()
#     await event_engine.startup()
#     await event_engine.register(event_type, event_process)
#     await event_engine.put(Event(event_type, event_data))
#     await event_engine.shutdown()
