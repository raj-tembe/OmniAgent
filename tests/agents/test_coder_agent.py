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


def test_coder_agent_publishes_file_diff_events_for_changed_files(monkeypatch):
    monkeypatch.setattr(
        "agents.coder.coder_agent.create_coder_chain",
        lambda: DummyChain(),
    )

    published = []
    monkeypatch.setattr(
        "agents.coder.coder_agent.bus.publish",
        lambda event: published.append(event),
    )

    state = AgentState(
        user_request="Create a markdown editor",
        generated_files={"app.py": "x = 1\n"},
        current_step="Build UI",
        plan=["Build UI"],
        session_id="session-abc",
        interactive=False,
    )

    coder_agent(state)

    # DummyChain fails -> fallback response reuses the SAME generated_files
    # (no actual change), so no diff should be published for this case
    assert published == []


def test_coder_agent_publishes_diff_when_files_actually_change():
    from agents.coder.coder_agent import coder_agent as real_coder_agent

    class ChangingChain:
        def invoke(self, payload):
            from schemas.coder_schema import CoderOutput
            return CoderOutput(
                generated_files={"app.py": "x = 2\n"},
                explanation="Updated x",
                coding_status="completed",
                next_agent="executor",
                project_name="proj",
                entry_point="app.py",
            )

    import agents.coder.coder_agent as coder_agent_module
    original_create_chain = coder_agent_module.create_coder_chain
    original_publish = coder_agent_module.bus.publish

    published = []
    coder_agent_module.create_coder_chain = lambda: ChangingChain()
    coder_agent_module.bus.publish = lambda event: published.append(event)

    try:
        state = AgentState(
            user_request="Create a markdown editor",
            generated_files={"app.py": "x = 1\n"},
            current_step="Build UI",
            plan=["Build UI"],
            session_id="session-xyz",
            interactive=False,
        )
        real_coder_agent(state)
    finally:
        coder_agent_module.create_coder_chain = original_create_chain
        coder_agent_module.bus.publish = original_publish

    assert len(published) == 1
    assert published[0].type == "file.diff"
    assert published[0].filename == "app.py"
    assert published[0].change_type == "modified"
    assert published[0].session_id == "session-xyz"
    assert "-x = 1" in published[0].diff
    assert "+x = 2" in published[0].diff
