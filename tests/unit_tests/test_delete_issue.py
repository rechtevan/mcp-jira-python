"""Unit tests for DeleteIssueTool."""

import asyncio
from unittest.mock import Mock

import pytest
from jira.exceptions import JIRAError

from mcp_jira_python.tools.delete_issue import DeleteIssueTool


@pytest.fixture
def mock_issue() -> Mock:
    """Mock issue."""
    return Mock()


@pytest.fixture
def mock_jira(mock_issue: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> DeleteIssueTool:
    """Create tool with mock Jira."""
    tool = DeleteIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestDeleteIssueTool:
    """Tests for DeleteIssueTool."""

    def test_execute_deletes_issue(
        self, tool: DeleteIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test deleting an issue."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        assert result[0].type == "text"
        assert "TEST-123" in result[0].text

        mock_jira.issue.assert_called_once_with("TEST-123")
        mock_issue.delete.assert_called_once()

    def test_execute_nonexistent_issue(self, tool: DeleteIssueTool, mock_jira: Mock) -> None:
        """Test deleting a nonexistent issue raises error."""
        mock_jira.issue.side_effect = JIRAError(status_code=404)

        with pytest.raises((JIRAError, Exception)):
            asyncio.run(tool.execute({"issueKey": "TEST-123"}))

    def test_requires_issue_key(self, tool: DeleteIssueTool) -> None:
        """Test that issueKey is required."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: DeleteIssueTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "delete_issue"
        assert "issueKey" in definition.inputSchema["properties"]
