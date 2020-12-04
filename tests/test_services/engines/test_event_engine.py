import asyncio
from typing import Callable, Coroutine, List

import pytest
from pydantic import BaseModel

from app.services.engines.event_engine import Event, EventEngine

pytestmark = pytest.mark.asyncio


class Content:
    text = ""


class Payload(BaseModel):
    msg: str
    instance: Content

    class Config:
        arbitrary_types_allowed = True


content_1 = Content()
content_2 = Content()
content_3 = Content()
content_4 = Content()
content_5 = Content()


async def process_1(payload: Payload) -> None:
    payload.instance.text = payload.msg


async def process_2(payload: Payload) -> None:
    payload.instance.text = payload.msg


async def process_3(payload: Payload) -> None:
    payload.instance.text += payload.msg


async def process_4(payload: Payload) -> None:
    payload.instance.text += payload.msg


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process, content",
    [
        ("foo_event", "foo", process_1, content_1),
        ("bar_event", "bar", process_2, content_2),
    ],
)
async def test_event_engine_can_run(
    event_engine: EventEngine,
    event_type: str,
    event_payload_msg: str,
    event_process: Callable[[Payload], Coroutine],
    content: Content,
):
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
    [
        ("foo_event", "foo", [process_3, process_4], content_3),
    ],
)
async def test_event_engine_can_handle_many_process_with_one_event(
    event_engine: EventEngine,
    event_type: List[str],
    event_payload_msg: str,
    event_process: List[Callable[[Payload], Coroutine]],
    content: Content,
):
    """测试事件引擎能否正确处理一个事件的多个流程."""
    for process in event_process:
        await event_engine.register("foo_event", process)
    payload = Payload(msg=event_payload_msg, instance=content)
    await event_engine.put(Event("foo_event", payload))
    await asyncio.sleep(1)
    assert content_3.text == 2 * event_payload_msg


@pytest.mark.parametrize(
    "event_type, event_payload_msg, event_process, content",
    [
        (["foo_event", "bar_event"], "foo", [process_3, process_4], content_4),
    ],
)
async def test_event_engine_can_handle_one_process_with_many_event(
    event_engine: EventEngine,
    event_type: List[str],
    event_payload_msg: str,
    event_process: List[Callable[[Payload], Coroutine]],
    content: Content,
):
    """测试事件引擎能否正确同时处理多个事件的一个流程."""
    for i, j in zip(event_type, event_process):
        await event_engine.register(i, j)
    payload = Payload(msg=event_payload_msg, instance=content)
    await event_engine.put(Event(event_type[0], payload))
    await asyncio.sleep(1)
    assert content.text == event_payload_msg
    await event_engine.put(Event(event_type[1], payload))
    await asyncio.sleep(1)
    assert content.text == 2 * event_payload_msg


async def test_event_engine_can_unregister_event(
    event_engine: EventEngine,
):
    """测试事件引擎能否正确注销事件特定流程."""
    await event_engine.register("foo_event", process_3)
    await event_engine.register("foo_event", process_4)
    await event_engine.unregister("foo_event", process_4)
    payload = Payload(msg="foo", instance=content_5)
    await event_engine.put(Event("foo_event", payload))
    await asyncio.sleep(1)
    assert content_5.text == "foo"
