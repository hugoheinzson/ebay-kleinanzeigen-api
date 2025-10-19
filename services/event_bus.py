"""Simple in-process event bus to fan out domain events to background services."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List, Type, TypeVar

from loguru import logger

EventT = TypeVar("EventT")
EventHandler = Callable[[EventT], Awaitable[None]]


class EventBus:
    """Lightweight asynchronous event bus with a single dispatcher task."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[object] = asyncio.Queue()
        self._subscribers: Dict[Type[object], List[EventHandler]] = defaultdict(list)
        self._dispatcher: asyncio.Task | None = None
        self._running = asyncio.Event()

    def subscribe(self, event_type: Type[EventT], handler: EventHandler[EventT]) -> None:
        """Register an asynchronous handler for the given event type."""

        self._subscribers[event_type].append(handler)  # type: ignore[arg-type]

    async def start(self) -> None:
        """Start the dispatcher loop if not already running."""

        if self._dispatcher is not None and not self._dispatcher.done():
            return

        self._running.set()
        self._dispatcher = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        """Stop the dispatcher loop and wait for graceful shutdown."""

        if self._dispatcher is None:
            return

        self._running.clear()
        await self._queue.put(None)  # Sentinel to unblock queue

        try:
            await self._dispatcher
        except asyncio.CancelledError:
            pass
        finally:
            self._dispatcher = None

    async def publish(self, event: object) -> None:
        """Enqueue an event for asynchronous fan-out."""

        await self._queue.put(event)

    async def _dispatch_loop(self) -> None:
        while self._running.is_set():
            event = await self._queue.get()
            if event is None:
                # Sentinel - allow graceful exit
                self._queue.task_done()
                break

            handlers = list(self._subscribers.get(type(event), []))
            if not handlers:
                logger.debug("No subscribers for event", event_type=type(event).__name__)
                self._queue.task_done()
                continue

            await self._fan_out(event, handlers)
            self._queue.task_done()

    async def _fan_out(self, event: object, handlers: List[EventHandler]) -> None:
        tasks = []
        for handler in handlers:
            tasks.append(asyncio.create_task(self._invoke_handler(handler, event)))

        if not tasks:
            return

        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception:
            logger.exception("Event handler raised exception", event_type=type(event).__name__)

    async def _invoke_handler(self, handler: EventHandler, event: object) -> None:
        try:
            await handler(event)  # type: ignore[arg-type]
        except Exception:
            logger.exception(
                "Event handler failed",
                handler=getattr(handler, "__name__", repr(handler)),
                event_type=type(event).__name__,
            )
