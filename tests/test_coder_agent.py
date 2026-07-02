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
