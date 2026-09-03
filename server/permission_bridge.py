"""
Bridges permission/engine.py's "ask" resolution to an HTTP round-trip
instead of a terminal `input()` prompt — the piece a GUI app with no
attached console actually needs.

Flow: PermissionEngine.check() calls the resolver returned by
make_server_resolver(), which registers a pending wait and blocks (on a
background thread — see server/sessions.py, every workflow run already
happens off the main thread) until either the desktop app POSTs a decision
to `/sessions/{id}/permission-response` (see server/app.py, which calls
`resolve()` below) or `timeout` elapses. A timeout resolves to `False`
(deny) — an unanswered prompt is a safe default, not an accidental allow.
"""
import threading
from typing import Dict, Optional


class PendingPermissionStore:
    """
    Tracks in-flight "ask" requests by their request_id, each waiting on a
    `threading.Event` until server/app.py's permission-response endpoint
    resolves it (or it times out).
    """

    def __init__(self):
        self._pending: Dict[str, threading.Event] = {}
        self._decisions: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def wait_for_resolution(self, request_id: str, timeout: float = 300.0) -> bool:
        """
        Block until `request_id` is resolved or `timeout` seconds pass.
        Returns the decision (True=allow), or False if it timed out.
        """
        event = threading.Event()
        with self._lock:
            self._pending[request_id] = event

        resolved_in_time = event.wait(timeout=timeout)

        with self._lock:
            self._pending.pop(request_id, None)
            decision = self._decisions.pop(request_id, False)

        return decision if resolved_in_time else False

    def resolve(self, request_id: str, approved: bool) -> bool:
        """
        Record a decision for `request_id` and wake up whoever's waiting on
        it. Returns False if there was no matching pending request (already
        resolved, timed out, or never existed) — callers use this to return
        404 rather than silently accepting a decision for nothing.
        """
        with self._lock:
            event = self._pending.get(request_id)
            if event is None:
                return False
            self._decisions[request_id] = approved

        event.set()
        return True


#process-wide singleton, same pattern as bus/event_bus.py and server/sessions.py
pending_permissions = PendingPermissionStore()


def make_server_resolver(store: Optional[PendingPermissionStore] = None, timeout: float = 300.0):
    """
    Build a `resolver` callable for PermissionEngine's constructor
    (see permission/engine.py) that waits on `store` instead of reading a
    terminal. `store` defaults to the process-wide `pending_permissions`
    singleton — pass a fresh one in tests to avoid cross-test interference.
    """
    store = store or pending_permissions

    def resolver(tool: str, agent: str, reason: Optional[str], request_id: str) -> bool:
        return store.wait_for_resolution(request_id, timeout=timeout)

    return resolver
