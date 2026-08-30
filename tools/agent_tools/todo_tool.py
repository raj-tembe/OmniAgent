from typing import Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

TodoStatus = Literal["pending", "in_progress", "completed"]


class TodoItem(BaseModel):
    """One entry in an agent's visible task list."""

    id: str = Field(default_factory=lambda: uuid4().hex[:8], description="Short unique id for this item.")
    content: str = Field(..., description="What this task is.")
    status: TodoStatus = Field(default="pending", description="Current status of this task.")


class TodoTool:
    """
    A visible, agent-maintained task list — the difference between "the
    planner has an internal plan" and "there's a list the user (and a future
    IDE panel) can actually see update in real time" as the agent works
    through it.

    Deliberately stateless: callers pass the current list in and get an
    updated list back, the same way every other agent node here reads state
    in and returns state deltas out. `graph/state.py`'s `todos` field is
    where the list actually lives between graph steps.
    """

    @staticmethod
    def write(items: List[str]) -> List[Dict]:
        """
        Replace the whole todo list with fresh items (all "pending") — the
        agent submits its full current plan, not an incremental diff.
        """
        return [TodoItem(content=item).model_dump() for item in items]

    @staticmethod
    def update_status(todos: List[Dict], item_id: str, status: TodoStatus) -> List[Dict]:
        """Update one item's status in place, leaving the rest untouched."""
        updated = []
        for todo in todos:
            if todo.get("id") == item_id:
                todo = {**todo, "status": status}
            updated.append(todo)
        return updated

    @staticmethod
    def read(todos: List[Dict]) -> Dict:
        """Summarize the current list — counts plus the raw items."""
        counts = {"pending": 0, "in_progress": 0, "completed": 0}
        for todo in todos:
            status = todo.get("status", "pending")
            if status in counts:
                counts[status] += 1

        return {"todos": todos, "counts": counts}
