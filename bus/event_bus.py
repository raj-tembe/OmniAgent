"""
In-process pub/sub event bus.

This is the backbone the CLI, plugins, and the permission engine all hang
off of. OmniAgent's LangGraph nodes publish events here; any number of
subscribers — a logger, the future IDE's live panel, a plugin, the
permission engine — can listen without the graph knowing they exist.

Deliberately synchronous and in-process for now: no network, no queue. If
OmniAgent grows a server mode (Phase 4), this is the module that gets an
SSE/websocket subscriber wired onto it — the publish/subscribe contract
itself doesn't need to change.
"""
import logging
import time
from collections import defaultdict
from typing import Callable, Dict, List, Type, TypeVar

from bus.events import AnyEvent, Event, EventType

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=Event)
Handler = Callable[[Event], None]

#subscribing with this key receives every event, regardless of type
WILDCARD: str = "*"


class EventBus:
    """
    Simple synchronous publish/subscribe event bus.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event_type: EventType | str, handler: Handler) -> Callable[[], None]:
        """
        Register `handler` for `event_type` (or `bus.WILDCARD` for everything).

        Returns an `unsubscribe` callable so callers don't need to keep the
        original handler reference around just to remove it later.
        """
        self._subscribers[event_type].append(handler)

        def unsubscribe() -> None:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass

        return unsubscribe

    def publish(self, event: AnyEvent) -> None:
        """
        Publish `event` to every handler registered for its type plus every
        wildcard handler. A handler that raises is logged and skipped —
        one broken subscriber (e.g. a third-party plugin) must never take
        down the agent workflow that published the event.
        """
        if event.timestamp is None:
            event.timestamp = time.time()

        for handler in (*self._subscribers.get(event.type, []), *self._subscribers.get(WILDCARD, [])):
            try:
                handler(event)
            except Exception:
                logger.exception("event handler failed for %s", event.type)

    def clear(self) -> None:
        """Remove all subscribers. Mainly for test isolation."""
        self._subscribers.clear()


#process-wide singleton — graph nodes and tools import and use this directly.
bus = EventBus()
