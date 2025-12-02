"""Unit tests for SearchMyIssuesTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.search_my_issues import SearchMyIssuesTool


@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock issue."""
    issue = Mock()
    issue.key = "PROJ-123"
    issue.fields.summary = "Test issue"
    issue.fields.status = Mock(__str__=lambda s: "In Progress")
    issue.fields.issuetype = Mock(__str__=lambda s: "Story")
    issue.fields.project.key = "PROJ"
    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.search_issues.return_value = [mock_issue]
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> SearchMyIssuesTool:
    """Create tool with mock Jira."""
    tool = SearchMyIssuesTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestSearchMyIssuesTool:
    """Tests for SearchMyIssuesTool."""

    def test_execute_default(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test default search (assignee, in_progress)."""
        result = asyncio.run(tool.execute({}))

        assert result[0].type == "text"
        data = json.loads(result[0].text)

        assert data["count"] == 1
        assert len(data["issues"]) == 1
        assert data["issues"][0]["key"] == "PROJ-123"
        assert data["statusFilter"] == "in_progress"
        assert data["roleFilter"] == "assignee"
        assert "hint" in data

        # Verify JQL contains assignee
        call_args = mock_jira.search_issues.call_args
        assert "assignee = currentUser()" in call_args[0][0]

    def test_execute_with_project(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search with project filter."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        assert data["projectFilter"] == "PROJ"

        call_args = mock_jira.search_issues.call_args
        assert "project = PROJ" in call_args[0][0]

    def test_execute_role_reporter(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search by reporter role."""
        result = asyncio.run(tool.execute({"role": "reporter"}))

        data = json.loads(result[0].text)
        assert data["roleFilter"] == "reporter"

        call_args = mock_jira.search_issues.call_args
        assert "reporter = currentUser()" in call_args[0][0]

    def test_execute_role_watcher(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search by watcher role."""
        result = asyncio.run(tool.execute({"role": "watcher"}))

        data = json.loads(result[0].text)
        assert data["roleFilter"] == "watcher"

        call_args = mock_jira.search_issues.call_args
        assert "watcher = currentUser()" in call_args[0][0]

    def test_execute_role_any(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search by any role."""
        result = asyncio.run(tool.execute({"role": "any"}))

        data = json.loads(result[0].text)
        assert data["roleFilter"] == "any"

        call_args = mock_jira.search_issues.call_args
        jql = call_args[0][0]
        assert "assignee = currentUser()" in jql
        assert "reporter = currentUser()" in jql
        assert "watcher = currentUser()" in jql

    def test_execute_status_open(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search with open status filter."""
        result = asyncio.run(tool.execute({"status": "open"}))

        data = json.loads(result[0].text)
        assert data["statusFilter"] == "open"

        call_args = mock_jira.search_issues.call_args
        assert "status != Done" in call_args[0][0]

    def test_execute_status_all(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search with all status filter."""
        result = asyncio.run(tool.execute({"status": "all"}))

        data = json.loads(result[0].text)
        assert data["statusFilter"] == "all"

    def test_execute_no_results(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test search with no results."""
        mock_jira.search_issues.return_value = []
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        assert data["count"] == 0
        assert "hint" not in data

    def test_execute_error(self, tool: SearchMyIssuesTool, mock_jira: Mock) -> None:
        """Test error handling."""
        mock_jira.search_issues.side_effect = Exception("API error")

        with pytest.raises(Exception, match="Failed to search issues"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: SearchMyIssuesTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "search_my_issues"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "status" in definition.inputSchema["properties"]
        assert "role" in definition.inputSchema["properties"]
