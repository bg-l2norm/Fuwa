import pytest
import asyncio
from infrastructure.events import EventBus

def test_subscribe_publish():
    bus = EventBus()
    received = []

    def on_event(data):
        received.append(data)

    bus.subscribe("test_event", on_event)
    bus.publish("test_event", data="hello")

    # Wait for the background thread to process
    bus._queue.join()

    assert received == ["hello"]

def test_multiple_subscribers():
    bus = EventBus()
    received1 = []
    received2 = []

    bus.subscribe("test_event", lambda x: received1.append(x))
    bus.subscribe("test_event", lambda x: received2.append(x))

    bus.publish("test_event", x=1)

    bus._queue.join()

    assert received1 == [1]
    assert received2 == [1]

def test_multiple_event_types():
    bus = EventBus()
    received_a = []
    received_b = []

    bus.subscribe("event_a", lambda: received_a.append(True))
    bus.subscribe("event_b", lambda: received_b.append(True))

    bus.publish("event_a")

    bus._queue.join()
    assert len(received_a) == 1
    assert len(received_b) == 0

def test_kwargs_passing():
    bus = EventBus()
    received = {}

    def on_event(a, b, c=None):
        received.update({"a": a, "b": b, "c": c})

    bus.subscribe("test_event", on_event)
    bus.publish("test_event", a=1, b=2, c=3)

    bus._queue.join()

    assert received == {"a": 1, "b": 2, "c": 3}

def test_async_callback():
    bus = EventBus()
    received = []

    async def on_event(data):
        await asyncio.sleep(0.01)
        received.append(data)

    bus.subscribe("test_event", on_event)
    bus.publish("test_event", data="async_hello")

    bus._queue.join()
    assert received == ["async_hello"]

def test_callback_exception(capsys):
    bus = EventBus()
    received = []

    def failing_callback():
        raise ValueError("Boom")

    def success_callback():
        received.append(True)

    bus.subscribe("test_event", failing_callback)
    bus.subscribe("test_event", success_callback)

    bus.publish("test_event")

    bus._queue.join()

    assert received == [True]
    captured = capsys.readouterr()
    assert "EventBus callback error: Boom" in captured.out
