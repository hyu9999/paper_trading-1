import asyncio

import pytest
from pydantic import BaseModel

from app.services.engines.event_engine import EventEngine, Event

pytestmark = pytest.mark.asyncio


class Payload(BaseModel):
    msg: str


class Content:
    def __init__(self):
        text = None


content = Content()


async def process_foo(payload: Payload) -> None:
    content.text = payload.msg


async def process_bar(payload: Payload) -> None:
    content.text = payload.msg


@pytest.fixture
async def event_engine():
    event_engine = EventEngine()
    await event_engine.startup()
    return event_engine


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process",
    (("foo_event", "foo", process_foo), ("bar_event", "bar", process_bar)),
)
async def test_event_engine_can_run(event_engine, event_type, event_payload_msg, event_process):
    """测试event engine是否能正确执行任务.

    任务内容为改变content实例的text值
    """
    payload = Payload(msg=event_payload_msg)
    await event_engine.register(event_type, event_process)
    await event_engine.put(Event(event_type, payload))
    await asyncio.sleep(3)
    assert content.text == event_payload_msg
    await event_engine.shutdown()
