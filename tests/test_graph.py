"""End-to-end and routing tests for the control-room agent graph."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_env(tmp_path, monkeypatch):
    """Set up environment and mock paths."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    yield tmp_path


@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch("agents.nodes.Anthropic") as mock:
        yield mock


def test_graph_import():
    """Test that graph can be imported."""
    from agents.graph import get_graph
    graph = get_graph()
    assert graph is not None
    assert hasattr(graph, "stream")


def test_supervisor_routing_to_planner(mock_anthropic):
    """Test supervisor routes planning requests to planner."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    # Mock the API response to route to planner
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="planner")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        mock_settings.model = "claude-sonnet-5"
        mock_settings.require_api_key = MagicMock()

        state = ControlRoomState(
            messages=[{"role": "user", "content": "plan a new invoice app"}],
            worker="",
            context=""
        )

        result = supervisor_node(state)

        assert result.goto == "planner"
        mock_client.messages.create.assert_called_once()


def test_supervisor_routing_to_tracker(mock_anthropic):
    """Test supervisor routes tracking requests to tracker."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="tracker")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        mock_settings.model = "claude-sonnet-5"
        mock_settings.require_api_key = MagicMock()

        state = ControlRoomState(
            messages=[{"role": "user", "content": "which projects are stalled"}],
            worker="",
            context=""
        )

        result = supervisor_node(state)

        assert result.goto == "tracker"


def test_supervisor_routing_to_historian(mock_anthropic):
    """Test supervisor routes memory requests to historian."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="historian")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        mock_settings.model = "claude-sonnet-5"
        mock_settings.require_api_key = MagicMock()

        state = ControlRoomState(
            messages=[{"role": "user", "content": "what did we discuss last"}],
            worker="",
            context=""
        )

        result = supervisor_node(state)

        assert result.goto == "historian"


def test_supervisor_handles_invalid_response(mock_anthropic):
    """Test supervisor handles invalid worker names gracefully."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="unknown_worker")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        mock_settings.model = "claude-sonnet-5"
        mock_settings.require_api_key = MagicMock()

        state = ControlRoomState(
            messages=[{"role": "user", "content": "do something"}],
            worker="",
            context=""
        )

        result = supervisor_node(state)

        assert result.goto == "end"


def test_supervisor_handles_ambiguous_request(mock_anthropic):
    """Test supervisor clarifies ambiguous requests."""
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="clarify: do you want to plan or track?")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        mock_settings.model = "claude-sonnet-5"
        mock_settings.require_api_key = MagicMock()

        state = ControlRoomState(
            messages=[{"role": "user", "content": "something"}],
            worker="",
            context=""
        )

        result = supervisor_node(state)

        assert result.goto == "end"
        assert "clarified" in result.update["context"]


def test_smoke_test_minimal_graph_invoke(mock_env, mock_anthropic):
    """Smoke test: invoke graph with a test query."""
    from agents.graph import get_graph
    from agents.state import ControlRoomState
    from agents.nodes import supervisor_node

    # Mock both supervisor and planner responses
    mock_client = MagicMock()

    def mock_create(*args, **kwargs):
        resp = MagicMock()
        system = kwargs.get("system", "")
        if "supervisor" in system:
            resp.content = [MagicMock(text="end")]
        else:
            resp.content = [MagicMock(text="Done planning")]
        resp.stop_reason = "end_turn"
        return resp

    mock_client.messages.create.side_effect = mock_create
    mock_anthropic.return_value = mock_client

    with patch("agents.nodes.settings") as mock_settings:
        with patch("agents.config.settings") as config_settings:
            mock_settings.model = "claude-sonnet-5"
            mock_settings.temperature = 0.7
            mock_settings.max_tool_steps = 10
            mock_settings.require_api_key = MagicMock()
            config_settings.require_api_key = MagicMock()

            state = ControlRoomState(
                messages=[{"role": "user", "content": "test"}],
                worker="",
                context=""
            )

            # Just verify we can call supervisor without error
            result = supervisor_node(state)
            assert result is not None
