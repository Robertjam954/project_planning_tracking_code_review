"""Unit tests for agent tools with mocked subprocess/gh calls."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.tools import (
    fetch_pr_reviews,
    new_agentic_project,
    read_history,
    read_status,
    recall_history,
)


@pytest.fixture
def mock_settings(tmp_path):
    """Mock settings with temporary paths."""
    with patch("agents.tools.settings") as m:
        m.scripts_dir = Path(__file__).parent.parent / "scripts"
        m.root = Path(__file__).parent.parent
        m.projects_json = tmp_path / "projects.json"
        m.todos_dir = tmp_path / "todos"
        m.history_json = tmp_path / "data" / "history.json"
        m.github_token = "ghp_test_token"
        yield m


def test_new_agentic_project_success(mock_settings):
    """Test new_agentic_project calls subprocess correctly."""
    with patch("agents.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="# Invoice Parser\n- [ ] Implement\n",
            stderr=""
        )

        result = new_agentic_project.invoke({
            "project_name": "Invoice Parser",
            "framework": "LangGraph"
        })

        assert "Invoice Parser" in result
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "new_agentic_project.py" in str(args)
        assert "Invoice Parser" in args
        assert "LangGraph" in args


def test_new_agentic_project_error(mock_settings):
    """Test new_agentic_project error handling."""
    with patch("agents.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="File not found"
        )

        result = new_agentic_project.invoke({
            "project_name": "Test",
            "framework": "FastAPI+Anthropic"
        })

        assert "Error" in result
        assert "File not found" in result


def test_read_status_empty(mock_settings, tmp_path):
    """Test read_status with no projects."""
    mock_settings.projects_json.write_text(json.dumps({
        "owner": "testuser",
        "tracks": []
    }))

    result = read_status.invoke({})
    data = json.loads(result)

    assert data == {}


def test_read_status_with_projects(mock_settings, tmp_path):
    """Test read_status counts todos correctly."""
    mock_settings.todos_dir.mkdir(parents=True, exist_ok=True)
    todo_file = mock_settings.todos_dir / "test-project.md"
    todo_file.write_text("""# Test Project
- [x] Done task
- [ ] Pending task 1
- [ ] Pending task 2
""")

    mock_settings.projects_json.write_text(json.dumps({
        "owner": "testuser",
        "tracks": [
            {
                "key": "test",
                "label": "Test Project",
                "todo": "test-project.md",
            }
        ]
    }))

    result = read_status.invoke({})
    data = json.loads(result)

    assert "test" in data
    assert data["test"]["done"] == 1
    assert data["test"]["total"] == 3


def test_read_history_empty(mock_settings):
    """Test read_history with no history."""
    result = read_history.invoke({})

    assert "No history" in result


def test_read_history_with_data(mock_settings, tmp_path):
    """Test read_history returns recent snapshots."""
    (tmp_path / "data").mkdir(exist_ok=True)
    history = {
        "snapshots": [
            {"date": "2026-07-01", "overall": {"done": 1, "total": 5}},
            {"date": "2026-07-02", "overall": {"done": 2, "total": 5}},
        ]
    }
    mock_settings.history_json.write_text(json.dumps(history))

    result = read_history.invoke({})
    data = json.loads(result)

    assert len(data) == 2
    assert data[-1]["date"] == "2026-07-02"


def test_fetch_pr_reviews_no_token():
    """Test fetch_pr_reviews without GitHub token."""
    with patch("agents.tools.settings") as mock_settings:
        mock_settings.github_token = None

        result = fetch_pr_reviews.invoke({})

        assert "not configured" in result


def test_fetch_pr_reviews_success():
    """Test fetch_pr_reviews with successful gh calls."""
    with patch("agents.tools.settings") as mock_settings:
        mock_settings.github_token = "ghp_test"
        mock_settings.projects_json = Path("/fake/projects.json")

        with patch("agents.tools.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps([
                    {
                        "number": 1,
                        "title": "Fix memory leak in agent loop",
                        "comments": ["Good catch", "Nice fix"]
                    }
                ])
            )

            with patch("agents.tools.json.loads", side_effect=[
                {"owner": "test", "tracks": [{"repo": "repo1"}]},
                json.loads(mock_run.return_value.stdout)
            ]):
                with patch("agents.tools.Path") as mock_path:
                    mock_path.return_value.read_text.return_value = json.dumps({
                        "owner": "test",
                        "tracks": [{"repo": "repo1"}]
                    })
                    result = fetch_pr_reviews.invoke({})

                    assert "checked" in result or "issue" in result.lower()


def test_fetch_pr_reviews_timeout_handling():
    """Test fetch_pr_reviews handles subprocess timeout gracefully."""
    with patch("agents.tools.settings") as mock_settings:
        mock_settings.github_token = "ghp_test"
        mock_settings.projects_json = Path("/fake/projects.json")

        with patch("agents.tools.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout=""),  # First repo fails
                MagicMock(returncode=0, stdout="[]"),  # Second repo succeeds
            ]

            with patch("agents.tools.json.loads") as mock_json:
                def json_side_effect(x):
                    if isinstance(x, str):
                        if x == "{}":
                            return {"owner": "test", "tracks": [{"repo": "r1"}, {"repo": "r2"}]}
                        elif x == "[]":
                            return []
                    raise ValueError()

                mock_json.side_effect = json_side_effect

                with patch("agents.tools.Path") as mock_path:
                    mock_path.return_value.read_text.return_value = json.dumps({
                        "owner": "test",
                        "tracks": [{"repo": "r1"}, {"repo": "r2"}]
                    })
                    result = fetch_pr_reviews.invoke({})

                    assert "Error" not in result or "continuing" in result


def test_recall_history_empty():
    """Test recall_history with no sessions."""
    with patch("agents.tools.ConversationStore") as mock_store:
        mock_inst = MagicMock()
        mock_inst.list_sessions.return_value = []
        mock_store.return_value = mock_inst

        result = recall_history.invoke({})

        assert "No conversation history" in result
        mock_inst.close.assert_called_once()


def test_recall_history_list_sessions():
    """Test recall_history lists sessions."""
    with patch("agents.tools.ConversationStore") as mock_store:
        mock_inst = MagicMock()
        mock_inst.list_sessions.return_value = [
            {"session_id": "s1", "title": "Planning", "n_messages": 5}
        ]
        mock_store.return_value = mock_inst

        result = recall_history.invoke({})

        assert "s1" in result
        assert "Planning" in result
        assert "5 messages" in result


def test_recall_history_search():
    """Test recall_history search by query."""
    with patch("agents.tools.ConversationStore") as mock_store:
        mock_inst = MagicMock()
        mock_msg = MagicMock()
        mock_msg.session_id = "s1"
        mock_msg.role = "assistant"
        mock_msg.content = "This is about invoice parsing"
        mock_inst.search.return_value = [mock_msg]
        mock_store.return_value = mock_inst

        result = recall_history.invoke({"query": "invoice"})

        assert "Found" in result
        assert "s1" in result
        assert "invoice" in result.lower()


def test_recall_history_get_session():
    """Test recall_history retrieves specific session."""
    with patch("agents.tools.ConversationStore") as mock_store:
        mock_inst = MagicMock()
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.content = "Plan an app"
        mock_inst.get_messages.return_value = [mock_msg]
        mock_store.return_value = mock_inst

        result = recall_history.invoke({"session_id": "s1"})

        assert "Session s1" in result
        assert "user" in result.lower()
