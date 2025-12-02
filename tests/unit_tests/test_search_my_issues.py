"""Unit tests for SearchMyIssuesTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.search_my_issues import SearchMyIssuesTool


@pytest.fixture
def mock_issues() -> list[Mock]:
    """Sample issues for current user."""
    issues = []
    for key, summary, status, issue_type in [
        ("PROJ-101", "Implement login", "In Progress", "Story"),
        ("PROJ-102", "Fix bug", "In Progress", "Bug"),
        ("DEV-50", "Update docs", "Open", "Task"),
    ]:
        issue = Mock()
        issue.key = key
        issue.fields = Mock()
        issue.fields.summary = summary
        issue.fields.status = Mock()
        issue.fields.status.__str__ = lambda self, s=status: s
        issue.fields.issuetype = Mock()
        issue.fields.issuetype.__str__ = lambda self, t=issue_type: t
        issue.fields.priority = Mock()
        issue.fields.priority.__str__ = lambda self: "Medium"
        issue.fields.project = Mock()
        issue.fields.project.key = key.split("-")[0]
        issues.append(issue)
    return issues


@pytest.fixture
def mock_jira(mock_issues: list[Mock]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.search_issues.return_value = mock_issues
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> SearchMyIssuesTool:
    """Create tool with mock Jira."""
    tool = SearchMyIssuesTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestSearchMyIssues:
    """Tests for SearchMyIssuesTool."""

    def test_returns_issues(self, tool: SearchMyIssuesTool) -> None:
        """Test that issues are returned."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        assert data["count"] == 3
        assert len(data["issues"]) == 3

    def test_issue_includes_commit_format(self, tool: SearchMyIssuesTool) -> None:
        """Test that issues include commit format hint."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        issue = data["issues"][0]
        assert issue["commitFormat"] == "PROJ-101: "

    def test_includes_hint(self, tool: SearchMyIssuesTool) -> None:
        """Test that result includes helpful hint."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        assert "hint" in data
        assert "git commit" in data["hint"]

    def test_default_assignee_filter(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test that default role filter is assignee."""
        _ = asyncio.run(tool.execute({}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "assignee = currentUser()" in jql

    def test_default_in_progress_filter(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test that default status filter is in_progress."""
        _ = asyncio.run(tool.execute({}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "In Progress" in jql

    def test_project_filter(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test filtering by project."""
        _ = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "project = PROJ" in jql

    def test_reporter_role(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test filtering by reporter role."""
        _ = asyncio.run(tool.execute({"role": "reporter"}))

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "reporter = currentUser()" in jql

    def test_tool_definition(self, tool: SearchMyIssuesTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "search_my_issues"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "status" in definition.inputSchema["properties"]
        assert "role" in definition.inputSchema["properties"]
