"""Unit tests for GetEpicIssuesTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_epic_issues import GetEpicIssuesTool


@pytest.fixture
def mock_epic() -> Mock:
    """Mock epic issue."""
    epic = Mock()
    epic.key = "PROJ-100"
    epic.fields = Mock()
    epic.fields.summary = "Authentication Epic"
    return epic


@pytest.fixture
def mock_child_issues() -> list[Mock]:
    """Sample child issues for an epic."""
    issues = []
    test_data = [
        ("PROJ-101", "Login page", "Story", "Done", 3),
        ("PROJ-102", "Password reset", "Story", "In Progress", 5),
        ("PROJ-103", "Session management", "Task", "Open", 2),
        ("PROJ-104", "Login bug fix", "Bug", "Done", 1),
    ]
    for key, summary, issue_type, status, points in test_data:
        issue = Mock()
        issue.key = key
        issue.fields = Mock()
        issue.fields.summary = summary
        issue.fields.issuetype = Mock()
        issue.fields.issuetype.__str__ = lambda self, t=issue_type: t
        issue.fields.status = Mock()
        issue.fields.status.__str__ = lambda self, s=status: s
        issue.fields.priority = Mock()
        issue.fields.priority.__str__ = lambda self: "Medium"
        issue.fields.assignee = None
        issue.fields.customfield_10001 = points  # Story points
        issues.append(issue)
    return issues


@pytest.fixture
def mock_jira(mock_epic: Mock, mock_child_issues: list[Mock]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_epic
    jira.search_issues.return_value = mock_child_issues
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetEpicIssuesTool:
    """Create tool with mock Jira."""
    tool = GetEpicIssuesTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetEpicIssues:
    """Tests for GetEpicIssuesTool."""

    def test_returns_epic_issues(self, tool: GetEpicIssuesTool) -> None:
        """Test that issues are returned."""
        result = asyncio.run(tool.execute({"epicKey": "PROJ-100"}))

        data = json.loads(result[0].text)
        assert data["epicKey"] == "PROJ-100"
        assert data["epicSummary"] == "Authentication Epic"
        assert len(data["issues"]) == 4

    def test_includes_progress_stats(self, tool: GetEpicIssuesTool) -> None:
        """Test that progress statistics are included."""
        result = asyncio.run(tool.execute({"epicKey": "PROJ-100"}))

        data = json.loads(result[0].text)
        progress = data["progress"]

        assert progress["totalIssues"] == 4
        assert progress["doneIssues"] == 2  # PROJ-101 and PROJ-104
        assert progress["percentComplete"] == 50.0
        assert progress["totalPoints"] == 11  # 3 + 5 + 2 + 1
        assert progress["donePoints"] == 4  # 3 + 1
        assert progress["pointsPercentComplete"] == 36.4  # 4/11

    def test_issue_includes_details(self, tool: GetEpicIssuesTool) -> None:
        """Test that issues include key, summary, type, status."""
        result = asyncio.run(tool.execute({"epicKey": "PROJ-100"}))

        data = json.loads(result[0].text)
        issue = data["issues"][0]

        assert issue["key"] == "PROJ-101"
        assert issue["summary"] == "Login page"
        assert issue["type"] == "Story"
        assert issue["status"] == "Done"
        assert issue["storyPoints"] == 3

    def test_default_filter_is_all(self, tool: GetEpicIssuesTool, mock_jira: Mock) -> None:
        """Test that default filter is 'all'."""
        _ = asyncio.run(tool.execute({"epicKey": "PROJ-100"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status != Done" not in jql
        assert "status = Done" not in jql

    def test_filter_open(self, tool: GetEpicIssuesTool, mock_jira: Mock) -> None:
        """Test filtering to open issues."""
        _ = asyncio.run(tool.execute({"epicKey": "PROJ-100", "status": "open"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status != Done" in jql

    def test_filter_done(self, tool: GetEpicIssuesTool, mock_jira: Mock) -> None:
        """Test filtering to done issues."""
        _ = asyncio.run(tool.execute({"epicKey": "PROJ-100", "status": "done"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "status = Done" in jql

    def test_requires_epic_key(self, tool: GetEpicIssuesTool) -> None:
        """Test that epicKey is required."""
        with pytest.raises(ValueError, match="epicKey is required"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: GetEpicIssuesTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "get_epic_issues"
        assert "epicKey" in definition.inputSchema["properties"]
        assert "status" in definition.inputSchema["properties"]
