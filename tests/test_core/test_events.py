"""Tests for the Event Bus system."""

import pytest
import asyncio
from uuid import uuid4
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.events import (
    EventBus,
    get_event_bus,
    init_event_bus,
    shutdown_event_bus,
)
from src.schemas.events import EventType, DealEvent


@pytest.fixture
async def event_bus():
    """Create and start a fresh event bus for each test."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


class TestEventBusLifecycle:
    """Test event bus lifecycle operations."""

    @pytest.mark.asyncio
    async def test_start_event_bus(self):
        """Test starting the event bus."""
        bus = EventBus()
        assert not bus.is_running

        await bus.start()
        assert bus.is_running

        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_event_bus(self):
        """Test stopping the event bus."""
        bus = EventBus()
        await bus.start()
        assert bus.is_running

        await bus.stop()
        assert not bus.is_running

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test starting an already running bus is idempotent."""
        bus = EventBus()
        await bus.start()
        await bus.start()  # Should not raise

        assert bus.is_running
        await bus.stop()


class TestEventPublishing:
    """Test event publishing functionality."""

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing an event."""
        deal_id = uuid4()

        event = await event_bus.publish(
            event_type=EventType.DEAL_CREATED,
            deal_id=deal_id,
            payload={"deal_name": "Test Deal"},
        )

        assert event.event_type == EventType.DEAL_CREATED
        assert event.deal_id == deal_id
        assert event.payload["deal_name"] == "Test Deal"

    @pytest.mark.asyncio
    async def test_publish_with_document_id(self, event_bus):
        """Test publishing event with document ID."""
        deal_id = uuid4()
        doc_id = uuid4()

        event = await event_bus.publish(
            event_type=EventType.DOCUMENT_UPLOADED,
            deal_id=deal_id,
            document_id=doc_id,
            payload={"filename": "test.pdf"},
        )

        assert event.document_id == doc_id

    @pytest.mark.asyncio
    async def test_publish_with_correlation_id(self, event_bus):
        """Test publishing event with correlation ID for tracing."""
        correlation_id = uuid4()

        event = await event_bus.publish(
            event_type=EventType.DEAL_UPDATED,
            correlation_id=correlation_id,
        )

        assert event.correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_publish_pre_constructed_event(self, event_bus):
        """Test publishing a pre-constructed event."""
        event = DealEvent(
            event_type=EventType.DEAL_CREATED,
            deal_id=uuid4(),
            payload={"test": "data"},
        )

        await event_bus.publish_event(event)
        # Event should be queued successfully


class TestEventSubscription:
    """Test event subscription functionality."""

    @pytest.mark.asyncio
    async def test_subscribe_to_event_type(self, event_bus):
        """Test subscribing to a specific event type."""
        received_events = []

        async def handler(event: DealEvent):
            received_events.append(event)

        event_bus.subscribe(EventType.DEAL_CREATED, handler)

        # Publish event
        await event_bus.publish(
            event_type=EventType.DEAL_CREATED,
            deal_id=uuid4(),
        )

        # Give time for processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.DEAL_CREATED

    @pytest.mark.asyncio
    async def test_handler_not_called_for_other_events(self, event_bus):
        """Test handler is not called for unsubscribed event types."""
        received_events = []

        async def handler(event: DealEvent):
            received_events.append(event)

        event_bus.subscribe(EventType.DEAL_CREATED, handler)

        # Publish different event type
        await event_bus.publish(
            event_type=EventType.DOCUMENT_UPLOADED,
            deal_id=uuid4(),
        )

        await asyncio.sleep(0.1)

        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_subscribe_all_wildcard(self, event_bus):
        """Test wildcard subscription receives all events."""
        received_events = []

        async def handler(event: DealEvent):
            received_events.append(event)

        event_bus.subscribe_all(handler)

        # Publish multiple event types
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await event_bus.publish(EventType.DOCUMENT_UPLOADED, deal_id=uuid4())
        await event_bus.publish(EventType.DEAL_UPDATED, deal_id=uuid4())

        await asyncio.sleep(0.2)

        assert len(received_events) == 3

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_bus):
        """Test multiple handlers for same event type."""
        handler1_calls = []
        handler2_calls = []

        async def handler1(event: DealEvent):
            handler1_calls.append(event)

        async def handler2(event: DealEvent):
            handler2_calls.append(event)

        event_bus.subscribe(EventType.DEAL_CREATED, handler1)
        event_bus.subscribe(EventType.DEAL_CREATED, handler2)

        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await asyncio.sleep(0.1)

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_handler(self, event_bus):
        """Test unsubscribing a handler."""
        received_events = []

        async def handler(event: DealEvent):
            received_events.append(event)

        event_bus.subscribe(EventType.DEAL_CREATED, handler)

        # Publish first event
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await asyncio.sleep(0.1)
        assert len(received_events) == 1

        # Unsubscribe
        result = event_bus.unsubscribe(EventType.DEAL_CREATED, handler)
        assert result == True

        # Publish second event
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await asyncio.sleep(0.1)

        # Should still be 1 since we unsubscribed
        assert len(received_events) == 1


class TestEventHistory:
    """Test event history functionality."""

    @pytest.mark.asyncio
    async def test_event_stored_in_history(self, event_bus):
        """Test events are stored in history."""
        deal_id = uuid4()

        await event_bus.publish(EventType.DEAL_CREATED, deal_id=deal_id)
        await asyncio.sleep(0.1)

        history = event_bus.get_event_history()
        assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_filter_history_by_event_type(self, event_bus):
        """Test filtering history by event type."""
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await event_bus.publish(EventType.DOCUMENT_UPLOADED, deal_id=uuid4())
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())

        await asyncio.sleep(0.2)

        history = event_bus.get_event_history(event_type=EventType.DEAL_CREATED)

        for event in history:
            assert event.event_type == EventType.DEAL_CREATED

    @pytest.mark.asyncio
    async def test_filter_history_by_deal_id(self, event_bus):
        """Test filtering history by deal ID."""
        deal_id = uuid4()
        other_deal_id = uuid4()

        await event_bus.publish(EventType.DEAL_CREATED, deal_id=deal_id)
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=other_deal_id)
        await event_bus.publish(EventType.DEAL_UPDATED, deal_id=deal_id)

        await asyncio.sleep(0.2)

        history = event_bus.get_event_history(deal_id=deal_id)

        for event in history:
            assert event.deal_id == deal_id

    @pytest.mark.asyncio
    async def test_history_limit(self, event_bus):
        """Test history respects limit parameter."""
        for _ in range(10):
            await event_bus.publish(EventType.DEAL_UPDATED, deal_id=uuid4())

        await asyncio.sleep(0.3)

        history = event_bus.get_event_history(limit=5)
        assert len(history) <= 5


class TestErrorHandling:
    """Test error handling in event bus."""

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash_bus(self, event_bus):
        """Test handler exceptions don't crash the bus."""
        async def failing_handler(event: DealEvent):
            raise ValueError("Handler error")

        async def working_handler(event: DealEvent):
            pass

        event_bus.subscribe(EventType.DEAL_CREATED, failing_handler)
        event_bus.subscribe(EventType.DEAL_CREATED, working_handler)

        # Should not raise
        await event_bus.publish(EventType.DEAL_CREATED, deal_id=uuid4())
        await asyncio.sleep(0.1)

        # Bus should still be running
        assert event_bus.is_running


class TestQueueManagement:
    """Test queue management."""

    @pytest.mark.asyncio
    async def test_queue_size_property(self, event_bus):
        """Test queue size tracking."""
        # Stop processing temporarily
        event_bus._running = False

        for i in range(5):
            await event_bus._queue.put(
                DealEvent(event_type=EventType.DEAL_CREATED, deal_id=uuid4())
            )

        assert event_bus.queue_size == 5

        # Restart and clean up
        event_bus._running = True


class TestGlobalEventBus:
    """Test global event bus singleton."""

    @pytest.mark.asyncio
    async def test_get_event_bus_returns_same_instance(self):
        """Test get_event_bus returns same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    @pytest.mark.asyncio
    async def test_init_and_shutdown_event_bus(self):
        """Test global init and shutdown."""
        bus = await init_event_bus()
        assert bus.is_running

        await shutdown_event_bus()
        # After shutdown, global should be cleared
