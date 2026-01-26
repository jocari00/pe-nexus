"""Event Bus implementation using asyncio.Queue for in-process messaging."""

import asyncio
import logging
import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Callable, Coroutine, Optional
from uuid import UUID, uuid4

from src.schemas.events import DealEvent, EventType

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[DealEvent], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async event bus for decoupled agent communication.

    Features:
    - Pub/sub pattern with asyncio.Queue
    - Event type filtering
    - Handler registration and management
    - Event persistence for audit trail
    - Graceful shutdown support
    """

    def __init__(self, max_queue_size: int = 1000):
        self._queue: asyncio.Queue[DealEvent] = asyncio.Queue(maxsize=max_queue_size)
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._max_history = 10000
        self._event_history: deque[DealEvent] = deque(maxlen=self._max_history)

    async def start(self) -> None:
        """Start the event bus processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus processor gracefully."""
        self._running = False

        if self._processor_task:
            # Wait for remaining events to process
            await self._queue.join()
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("Event bus stopped")

    async def publish(
        self,
        event_type: EventType,
        deal_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        agent_name: Optional[str] = None,
        payload: Optional[dict] = None,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
    ) -> DealEvent:
        """
        Publish an event to the bus.

        Args:
            event_type: Type of event
            deal_id: Associated deal ID
            document_id: Associated document ID
            agent_name: Name of publishing agent
            payload: Event-specific data
            correlation_id: ID for tracing related events
            causation_id: ID of event that caused this one

        Returns:
            The published DealEvent
        """
        event = DealEvent(
            event_type=event_type,
            deal_id=deal_id,
            document_id=document_id,
            agent_name=agent_name,
            payload=payload or {},
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        await self._queue.put(event)
        logger.debug(f"Published event: {event_type.value} for deal {deal_id}")

        return event

    async def publish_event(self, event: DealEvent) -> None:
        """Publish a pre-constructed event."""
        await self._queue.put(event)
        logger.debug(f"Published event: {event.event_type.value}")

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: The event type to subscribe to
            handler: Async function to handle the event
        """
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.value}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to all event types."""
        self._wildcard_handlers.append(handler)
        logger.debug("Wildcard handler subscribed")

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Returns True if handler was found and removed.
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        return False

    async def _process_events(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                # Wait for event with timeout to allow graceful shutdown
                try:
                    event = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Store in history
                self._store_event(event)

                # Get handlers for this event type
                handlers = self._handlers.get(event.event_type, [])
                all_handlers = handlers + self._wildcard_handlers

                if not all_handlers:
                    logger.debug(f"No handlers for event type: {event.event_type.value}")
                    self._queue.task_done()
                    continue

                # Execute all handlers concurrently
                tasks = [
                    self._safe_execute(handler, event)
                    for handler in all_handlers
                ]
                await asyncio.gather(*tasks)

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _safe_execute(
        self,
        handler: EventHandler,
        event: DealEvent,
    ) -> None:
        """Execute a handler with error handling."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Handler error for {event.event_type.value}: {e}",
                exc_info=True,
            )

    def _store_event(self, event: DealEvent) -> None:
        """Store event in history for audit trail.

        Uses deque with maxlen for O(1) bounded history management.
        """
        self._event_history.append(event)

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        deal_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[DealEvent]:
        """
        Get events from history with optional filtering.

        Args:
            event_type: Filter by event type
            deal_id: Filter by deal ID
            limit: Maximum events to return

        Returns:
            List of matching events (most recent first)
        """
        # Filter directly with generator, then slice for efficiency
        events = [
            e for e in self._event_history
            if (not event_type or e.event_type == event_type)
            and (not deal_id or e.deal_id == deal_id)
        ]
        return list(reversed(events[-limit:]))

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if event bus is running."""
        return self._running


# Global event bus instance
_event_bus: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance (thread-safe)."""
    global _event_bus
    if _event_bus is None:
        with _event_bus_lock:
            # Double-check locking pattern
            if _event_bus is None:
                _event_bus = EventBus()
    return _event_bus


async def init_event_bus() -> EventBus:
    """Initialize and start the global event bus."""
    bus = get_event_bus()
    await bus.start()
    return bus


async def shutdown_event_bus() -> None:
    """Shutdown the global event bus."""
    global _event_bus
    if _event_bus:
        await _event_bus.stop()
        _event_bus = None
