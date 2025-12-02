"""Unit tests for GetTransitionsTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_transitions import GetTransitionsTool


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
            "fields": {
                "resolution": {
                    "required": True,
                    "name": "Resolution",
                }
            },
        },
        {
            "id": "31",
            "name": "Block",
            "to": {"name": "Blocked", "id": "5"},
        },
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
def mock_jira(mock_issue: Mock, mock_transitions: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    jira.transitions.return_value = mock_transitions
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetTransitionsTool:
    """Create tool with mock Jira."""
    tool = GetTransitionsTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetTransitions:
    """Tests for GetTransitionsTool."""

    def test_returns_available_transitions(self, tool: GetTransitionsTool) -> None:
        """Test that available transitions are returned."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        assert data["issueKey"] == "TEST-123"
        assert data["currentStatus"] == "Open"
        assert len(data["availableTransitions"]) == 3

    def test_transition_includes_id_and_name(self, tool: GetTransitionsTool) -> None:
        """Test that transitions include ID and name."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        transitions = data["availableTransitions"]

        assert transitions[0]["id"] == "11"
        assert transitions[0]["name"] == "Start Progress"
        assert transitions[0]["to"] == "In Progress"

    def test_includes_required_fields(self, tool: GetTransitionsTool) -> None:
        """Test that required fields are included for transitions that have them."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        transitions = data["availableTransitions"]

        # Find the "Done" transition which has required fields
        done_transition = next(t for t in transitions if t["name"] == "Done")
        assert "requiredFields" in done_transition
        assert done_transition["requiredFields"][0]["name"] == "Resolution"

    def test_excludes_required_fields_when_none(self, tool: GetTransitionsTool) -> None:
        """Test that requiredFields is not included when there are none."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        transitions = data["availableTransitions"]

        # "Start Progress" has no required fields
        start_transition = next(t for t in transitions if t["name"] == "Start Progress")
        assert "requiredFields" not in start_transition

    def test_requires_issue_key(self, tool: GetTransitionsTool) -> None:
        """Test that issueKey is required."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: GetTransitionsTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "get_transitions"
        assert "issueKey" in definition.inputSchema["properties"]
        assert "issueKey" in definition.inputSchema["required"]

