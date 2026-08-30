from langchain_core.exceptions import OutputParserException

from agents.coder.coder_agent import coder_agent
from graph.state import AgentState


class DummyChain:
    def invoke(self, payload):
        raise OutputParserException(None, "incomplete response")


def test_coder_agent_uses_fallback_when_structured_output_fails(monkeypatch):
    monkeypatch.setattr(
        "agents.coder.coder_agent.create_coder_chain",
        lambda: DummyChain(),
    )

    state = AgentState(
        user_request="Create a markdown editor",
        generated_files={"app.py": "print('hello')"},
        current_step="Generate app",
        plan=["Build UI"],
        interactive=False,
    )

    result = coder_agent(state)

    assert result["generated_files"] == {"app.py": "print('hello')"}
    assert result["coding_status"] == "completed"
    assert result["next_agent"] == "executor"
    assert result["entry_point"] == "app.py"
    assert result["coding_explanation"].startswith("Generated project files")


def test_coder_agent_initializes_todos_from_plan(monkeypatch):
    monkeypatch.setattr(
        "agents.coder.coder_agent.create_coder_chain",
        lambda: DummyChain(),
    )

    state = AgentState(
        user_request="Create a markdown editor",
        generated_files={},
        current_step="Build UI",
        plan=["Build UI", "Add save button"],
        interactive=False,
    )

    result = coder_agent(state)

    todos = result["todos"]
    assert len(todos) == 2
    assert {t["content"] for t in todos} == {"Build UI", "Add save button"}
    # the item matching current_step should have moved to in_progress
    matching = next(t for t in todos if t["content"] == "Build UI")
    assert matching["status"] == "in_progress"
    other = next(t for t in todos if t["content"] == "Add save button")
    assert other["status"] == "pending"


def test_coder_agent_preserves_existing_todos_across_calls(monkeypatch):
    monkeypatch.setattr(
        "agents.coder.coder_agent.create_coder_chain",
        lambda: DummyChain(),
    )

    existing_todos = [
        {"id": "abc123", "content": "Build UI", "status": "completed"},
        {"id": "def456", "content": "Add save button", "status": "pending"},
    ]

    state = AgentState(
        user_request="Create a markdown editor",
        generated_files={},
        current_step="Add save button",
        plan=["Build UI", "Add save button"],
        todos=existing_todos,
        interactive=False,
    )

    result = coder_agent(state)

    todos = result["todos"]
    completed = next(t for t in todos if t["content"] == "Build UI")
    assert completed["status"] == "completed"  # untouched, not reset
    in_progress = next(t for t in todos if t["content"] == "Add save button")
    assert in_progress["status"] == "in_progress"
