import asyncio

import pytest
from pydantic import BaseModel

from app.services.engines.event_engine import Event

pytestmark = pytest.mark.asyncio


class Content:
    text = ""


class Payload(BaseModel):
    msg: str
    instance: Content

    class Config:
        arbitrary_types_allowed = True


content_foo = Content()
content_bar = Content()
content_foo_bar = Content()
content_bar_foo = Content()


async def process_foo(payload: Payload) -> None:
    payload.instance.text = payload.msg


async def process_bar(payload: Payload) -> None:
    payload.instance.text = payload.msg


async def process_foo_1(payload: Payload) -> None:
    payload.instance.text += payload.msg


async def process_bar_1(payload: Payload) -> None:
    payload.instance.text += payload.msg


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process, content",
    (("foo_event", "foo", process_foo, content_foo), ("bar_event", "bar", process_bar, content_bar)),
)
async def test_event_engine_can_run(event_engine, event_type, event_payload_msg, event_process, content):
    """测试event engine是否能正确执行任务.

    任务内容为改变content实例的text值.
    """
    await event_engine.register(event_type, event_process)
    payload = Payload(msg=event_payload_msg, instance=content)
    await event_engine.put(Event(event_type, payload))
    await asyncio.sleep(1)
    assert content.text == event_payload_msg


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process, content",
    (
        ("foo_event", "foo", [process_foo_1, process_bar_1], content_foo_bar),
    ),
)
async def test_event_engine_can_handle_many_process_with_one_event(event_engine, event_type, event_payload_msg,
                                                                   event_process, content):
    """测试事件引擎能否正确处理一个事件的多个流程."""
    for process in event_process:
        await event_engine.register("foo_event", process)
    payload = Payload(msg=event_payload_msg, instance=content)
    await event_engine.put(Event("foo_event", payload))
    await asyncio.sleep(1)
    assert content_foo_bar.text == 2 * event_payload_msg


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process, content",
    (
        (["foo_event", "bar_event"], "foo", [process_foo_1, process_bar_1], content_bar_foo),
    ),
)
async def test_event_engine_can_handle_one_process_with_many_event(event_engine, event_type, event_payload_msg,
                                                                   event_process, content):
    """测试事件引擎能否正确处理多个事件的一个流程."""
    for i, j in zip(event_type, event_process):
        await event_engine.register(i, j)
    payload = Payload(msg=event_payload_msg, instance=content)
    await event_engine.put(Event(event_type[0], payload))
    await asyncio.sleep(1)
    assert content.text == event_payload_msg
    await event_engine.put(Event(event_type[1], payload))
    await asyncio.sleep(1)
    assert content.text == 2 * event_payload_msg
