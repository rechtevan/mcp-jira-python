"""Unit tests for TransitionIssueTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.transition_issue import TransitionIssueTool


@pytest.fixture
def mock_transitions() -> list[dict]:
    """Sample transitions data."""
    return [
        {
            "id": "11",
            "name": "Start Progress",
            "to": {"name": "In Progress", "id": "3"},
        },
        {
            "id": "21",
            "name": "Done",
            "to": {"name": "Done", "id": "4"},
        },
        {
            "id": "31",
            "name": "Block",
            "to": {"name": "Blocked", "id": "5"},
        },
    ]


@pytest.fixture
def mock_fields() -> list[dict]:
    """Sample field data."""
    return [
        {"id": "resolution", "name": "Resolution", "custom": False},
        {"id": "customfield_10001", "name": "Story Points", "custom": True},
    ]


@pytest.fixture
def mock_issue() -> Mock:
    """Mock issue."""
    issue = Mock()
    issue.fields = Mock()
    issue.fields.status = Mock()
    issue.fields.status.__str__ = lambda self: "Open"
    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock, mock_transitions: list[dict], mock_fields: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    jira.transitions.return_value = mock_transitions
    jira.fields.return_value = mock_fields
    jira.transition_issue.return_value = None
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> TransitionIssueTool:
    """Create tool with mock Jira."""
    tool = TransitionIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestTransitionIssue:
    """Tests for TransitionIssueTool."""

    def test_transition_by_name(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test transitioning by transition name."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "transition": "Done"}))

        data = json.loads(result[0].text)
        assert data["issueKey"] == "TEST-123"
        assert data["from"] == "Open"
        assert data["to"] == "Done"
        assert data["transition"] == "Done"

        # Verify API called with correct transition ID
        mock_jira.transition_issue.assert_called_once()
        call_args = mock_jira.transition_issue.call_args
        assert call_args[0][0] == "TEST-123"
        assert call_args[0][1] == "21"  # ID for "Done"

    def test_transition_by_id(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test transitioning by transition ID."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "transition": "11"}))

        data = json.loads(result[0].text)
        assert data["transition"] == "Start Progress"

        mock_jira.transition_issue.assert_called_once()
        call_args = mock_jira.transition_issue.call_args
        assert call_args[0][1] == "11"

    def test_transition_case_insensitive(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test that transition name matching is case-insensitive."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "transition": "done"}))

        data = json.loads(result[0].text)
        assert data["transition"] == "Done"

    def test_transition_partial_match(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test that partial transition names work."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "transition": "progress"}))

        data = json.loads(result[0].text)
        assert data["transition"] == "Start Progress"

    def test_transition_with_comment(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test transitioning with a comment."""
        result = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "transition": "Done",
                    "comment": "Completed the work",
                }
            )
        )

        data = json.loads(result[0].text)
        assert data["comment"] == "Added"

        call_args = mock_jira.transition_issue.call_args
        assert call_args.kwargs["comment"] == "Completed the work"

    def test_transition_with_fields(self, tool: TransitionIssueTool, mock_jira: Mock) -> None:
        """Test transitioning with additional fields."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "transition": "Done",
                    "fields": {"resolution": {"name": "Fixed"}},
                }
            )
        )

        call_args = mock_jira.transition_issue.call_args
        assert "fields" in call_args.kwargs
        assert call_args.kwargs["fields"]["resolution"] == {"name": "Fixed"}

    def test_transition_with_custom_field_by_name(
        self, tool: TransitionIssueTool, mock_jira: Mock
    ) -> None:
        """Test transitioning with custom field using friendly name."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "transition": "Done",
                    "fields": {"Story Points": 5},
                }
            )
        )

        call_args = mock_jira.transition_issue.call_args
        # Should translate "Story Points" to "customfield_10001"
        assert call_args.kwargs["fields"]["customfield_10001"] == 5

    def test_invalid_transition_raises_error(
        self, tool: TransitionIssueTool, mock_jira: Mock
    ) -> None:
        """Test that invalid transition raises helpful error."""
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(tool.execute({"issueKey": "TEST-123", "transition": "InvalidState"}))

        error_msg = str(exc_info.value)
        assert "InvalidState" in error_msg
        assert "Available transitions" in error_msg
        assert "Done" in error_msg

    def test_requires_issue_key(self, tool: TransitionIssueTool) -> None:
        """Test that issueKey is required."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({"transition": "Done"}))

    def test_requires_transition(self, tool: TransitionIssueTool) -> None:
        """Test that transition is required."""
        with pytest.raises(ValueError, match="transition is required"):
            asyncio.run(tool.execute({"issueKey": "TEST-123"}))

    def test_tool_definition(self, tool: TransitionIssueTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "transition_issue"
        assert "issueKey" in definition.inputSchema["properties"]
        assert "transition" in definition.inputSchema["properties"]
        assert "comment" in definition.inputSchema["properties"]
        assert "fields" in definition.inputSchema["properties"]
