"""
Session manager for server mode.

`run_workflow` (main.py) is fully synchronous and can run for a long time —
exactly the shape the IDE (or any HTTP client) needs to *not* block on.
This module runs each session in a background thread, and taps the event
bus (bus/) to build a per-session, in-order event log that a streaming HTTP
endpoint can tail — see server/app.py's `/sessions/{id}/events` route.

Threading, not asyncio, on purpose: `run_workflow` and everything it calls
(the whole LangGraph, every agent, every tool) is synchronous code written
with no `await` anywhere. Wrapping it in a thread is the smallest change
that makes it non-blocking from the server's point of view; a full
synchronous-to-async rewrite of the agent stack is out of scope here.
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from bus import AnyEvent, bus


@dataclass
class SessionRecord:
    session_id: str
    status: str = "running"  # "running" | "completed" | "error"
    result: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def append_event(self, event: AnyEvent) -> None:
        with self._lock:
            self.events.append(event.model_dump())

    def events_from(self, offset: int) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.events[offset:])


class SessionManager:
    """
    Holds every session started this process's lifetime, in memory. No
    persistence across restarts — `graph/checkpoint.py`'s LangGraph
    checkpointer is the durability layer for workflow state itself; this
    only tracks the HTTP-facing session/event bookkeeping on top of it.
    """

    def __init__(self, run_workflow_fn=None):
        self._sessions: Dict[str, SessionRecord] = {}
        self._lock = threading.Lock()
        # injectable for tests — avoids every test needing a real LLM call
        self._run_workflow_fn = run_workflow_fn

    def _get_run_workflow_fn(self):
        if self._run_workflow_fn is not None:
            return self._run_workflow_fn
        from main import run_workflow
        return run_workflow

    def create_session(
        self,
        user_request: str,
        agent_mode: str = "build",
        auto_approve: bool = False,
        interactive: bool = False,
    ) -> str:
        """Start a new session and return its id immediately (the workflow runs in the background)."""
        session_id = uuid.uuid4().hex
        record = SessionRecord(session_id=session_id)

        with self._lock:
            self._sessions[session_id] = record

        unsubscribe = bus.subscribe("*", self._make_event_handler(session_id, record))

        def worker():
            try:
                run_workflow_fn = self._get_run_workflow_fn()
                result = run_workflow_fn(
                    user_request=user_request,
                    interactive=interactive,
                    agent_mode=agent_mode,
                    auto_approve=auto_approve,
                    session_id=session_id,
                )
                record.result = result
                record.status = "error" if result.get("error") else "completed"
            except Exception as exc:
                record.result = {"success": False, "error": str(exc)}
                record.status = "error"
            finally:
                unsubscribe()

        threading.Thread(target=worker, daemon=True).start()
        return session_id

    def _make_event_handler(self, session_id: str, record: SessionRecord):
        def handler(event: AnyEvent) -> None:
            if getattr(event, "session_id", None) == session_id:
                record.append_event(event)
        return handler

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        with self._lock:
            return self._sessions.get(session_id)


#process-wide singleton, the same pattern bus/event_bus.py uses
session_manager = SessionManager()
