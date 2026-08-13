"""End-to-end and routing tests for the control-room agent graph.

The workers and supervisor were refactored onto the LangChain agent template
(`create_agent` + `init_chat_model`). These tests mock the shared chat model
(`agents.nodes._get_model`) rather than a raw provider client.
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """Set up environment for tests that touch config."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    yield tmp_path


def _model_returning(text: str) -> MagicMock:
    """A mock chat model whose .invoke(...) returns a message with `text`."""
    model = MagicMock()
    message = MagicMock()
    message.content = text
    model.invoke.return_value = message
    return model


def _route_with(text: str):
    """Run supervisor_node with a mocked model returning `text`; return the Command."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    with patch("agents.nodes._get_model", return_value=_model_returning(text)), patch(
        "agents.nodes.settings"
    ) as mock_settings:
        mock_settings.require_api_key = MagicMock()
        state = ControlRoomState(
            messages=[{"role": "user", "content": "some request"}],
            worker="",
            context="",
        )
        return supervisor_node(state)


def test_graph_import():
    """Test that graph can be imported and compiled."""
    from agents.graph import get_graph

    graph = get_graph()
    assert graph is not None
    assert hasattr(graph, "stream")


def test_supervisor_routing_to_planner():
    """Supervisor routes planning requests to planner."""
    result = _route_with("planner")
    assert result.goto == "planner"


def test_supervisor_routing_to_tracker():
    """Supervisor routes tracking requests to tracker."""
    result = _route_with("tracker")
    assert result.goto == "tracker"


def test_supervisor_routing_to_historian():
    """Supervisor routes memory requests to historian."""
    result = _route_with("historian")
    assert result.goto == "historian"


def test_supervisor_handles_invalid_response():
    """Supervisor handles invalid worker names gracefully (-> end)."""
    result = _route_with("unknown_worker")
    assert result.goto == "end"


def test_supervisor_handles_ambiguous_request():
    """Supervisor clarifies ambiguous requests (-> end, context=clarified)."""
    result = _route_with("clarify: do you want to plan or track?")
    assert result.goto == "end"
    assert "clarified" in result.update["context"]


def test_supervisor_handles_list_content():
    """Supervisor tolerates block-list message content (not just a string)."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    model = MagicMock()
    message = MagicMock()
    message.content = [{"type": "text", "text": "reviewer"}]
    model.invoke.return_value = message

    with patch("agents.nodes._get_model", return_value=model), patch(
        "agents.nodes.settings"
    ) as mock_settings:
        mock_settings.require_api_key = MagicMock()
        state = ControlRoomState(
            messages=[{"role": "user", "content": "review code quality"}],
            worker="",
            context="",
        )
        result = supervisor_node(state)

    assert result.goto == "reviewer"


def test_smoke_test_minimal_graph_invoke(mock_env):
    """Smoke test: supervisor routes to end without error when model says 'end'."""
    result = _route_with("end")
    assert result is not None
    assert result.goto == "end"
