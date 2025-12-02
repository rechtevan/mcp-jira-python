"""Unit tests for ListEpicsTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.list_epics import ListEpicsTool


@pytest.fixture
def mock_epics() -> list[Mock]:
    """Sample epic issues."""
    epics = []
    for i, (key, summary, status) in enumerate(
        [
            ("PROJ-100", "Authentication Epic", "In Progress"),
            ("PROJ-101", "User Management Epic", "Open"),
            ("PROJ-102", "Reporting Epic", "Done"),
        ]
    ):
        epic = Mock()
        epic.key = key
        epic.fields = Mock()
        epic.fields.summary = summary
        epic.fields.status = Mock()
        epic.fields.status.__str__ = lambda self, s=status: s
        epic.fields.priority = Mock()
        epic.fields.priority.__str__ = lambda self: "High"
        epic.fields.assignee = Mock()
        epic.fields.assignee.__str__ = lambda self, idx=i: f"user{idx}@example.com"
        epics.append(epic)
    return epics


@pytest.fixture
def mock_jira(mock_epics: list[Mock]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.search_issues.return_value = mock_epics
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> ListEpicsTool:
    """Create tool with mock Jira."""
    tool = ListEpicsTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestListEpics:
    """Tests for ListEpicsTool."""

    def test_returns_epics(self, tool: ListEpicsTool) -> None:
        """Test that epics are returned."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        assert data["projectKey"] == "PROJ"
        assert data["count"] == 3
        assert len(data["epics"]) == 3

    def test_epic_includes_key_and_summary(self, tool: ListEpicsTool) -> None:
        """Test that epics include key and summary."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        epic = data["epics"][0]
        assert epic["key"] == "PROJ-100"
        assert epic["summary"] == "Authentication Epic"
        assert epic["status"] == "In Progress"

    def test_default_filter_is_open(self, tool: ListEpicsTool, mock_jira: Mock) -> None:
        """Test that default filter is 'open'."""
        _ = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status != Done" in jql

    def test_filter_done(self, tool: ListEpicsTool, mock_jira: Mock) -> None:
        """Test filtering to done epics."""
        _ = asyncio.run(tool.execute({"projectKey": "PROJ", "status": "done"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status = Done" in jql

    def test_filter_all(self, tool: ListEpicsTool, mock_jira: Mock) -> None:
        """Test filtering to all epics."""
        _ = asyncio.run(tool.execute({"projectKey": "PROJ", "status": "all"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status != Done" not in jql
        assert "status = Done" not in jql

    def test_respects_max_results(self, tool: ListEpicsTool, mock_jira: Mock) -> None:
        """Test that maxResults is passed to API."""
        _ = asyncio.run(tool.execute({"projectKey": "PROJ", "maxResults": 10}))

        call_args = mock_jira.search_issues.call_args
        assert call_args.kwargs["maxResults"] == 10

    def test_requires_project_key(self, tool: ListEpicsTool) -> None:
        """Test that projectKey is required."""
        with pytest.raises(ValueError, match="projectKey is required"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: ListEpicsTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "list_epics"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "status" in definition.inputSchema["properties"]
