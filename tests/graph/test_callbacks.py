from graph.workflow import OmniAgentCallbacks


def test_callback_handler_flags_available():
    callbacks = OmniAgentCallbacks()
    assert callbacks.raise_error is False
    assert callbacks.ignore_chain is False
    assert callbacks.ignore_agent is False
    assert callbacks.ignore_llm is False
