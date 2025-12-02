"""Unit tests for FormatCommitTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.format_commit import FormatCommitTool


@pytest.fixture
def mock_issue() -> Mock:
    """Mock issue for validation."""
    issue = Mock()
    issue.key = "PROJ-123"
    issue.fields = Mock()
    issue.fields.summary = "Implement user authentication"
    issue.fields.issuetype = Mock()
    issue.fields.issuetype.__str__ = lambda self: "Story"
    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> FormatCommitTool:
    """Create tool with mock Jira."""
    tool = FormatCommitTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestFormatCommit:
    """Tests for FormatCommitTool."""

    def test_basic_format(self, tool: FormatCommitTool) -> None:
        """Test basic commit message format."""
        result = asyncio.run(tool.execute({"issueKey": "PROJ-123", "message": "Add login form"}))

        data = json.loads(result[0].text)
        assert data["commitMessage"] == "PROJ-123: Add login form"
        assert data["issueKey"] == "PROJ-123"

    def test_conventional_commit_format(self, tool: FormatCommitTool) -> None:
        """Test conventional commit format with type."""
        result = asyncio.run(
            tool.execute(
                {
                    "issueKey": "PROJ-123",
                    "message": "add login form",
                    "type": "feat",
                }
            )
        )

        data = json.loads(result[0].text)
        assert data["commitMessage"] == "feat(PROJ-123): add login form"

    def test_includes_git_command(self, tool: FormatCommitTool) -> None:
        """Test that git command is included."""
        result = asyncio.run(tool.execute({"issueKey": "PROJ-123", "message": "Add feature"}))

        data = json.loads(result[0].text)
        assert "gitCommand" in data
        assert "git commit -m" in data["gitCommand"]

    def test_uppercase_issue_key(self, tool: FormatCommitTool) -> None:
        """Test that issue key is uppercased."""
        result = asyncio.run(tool.execute({"issueKey": "proj-123", "message": "Add feature"}))

        data = json.loads(result[0].text)
        assert data["issueKey"] == "PROJ-123"

    def test_include_description(self, tool: FormatCommitTool) -> None:
        """Test including issue description in commit."""
        result = asyncio.run(
            tool.execute(
                {
                    "issueKey": "PROJ-123",
                    "message": "Add feature",
                    "includeDescription": True,
                }
            )
        )

        data = json.loads(result[0].text)
        assert "Related to: Implement user authentication" in data["commitMessage"]
        assert "Issue type: Story" in data["commitMessage"]

    def test_validates_issue_exists(self, tool: FormatCommitTool, mock_jira: Mock) -> None:
        """Test that issue existence is validated by default."""
        _ = asyncio.run(tool.execute({"issueKey": "PROJ-123", "message": "Add feature"}))

        mock_jira.issue.assert_called_once()

    def test_skip_validation(self, tool: FormatCommitTool, mock_jira: Mock) -> None:
        """Test skipping validation."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "PROJ-123",
                    "message": "Add feature",
                    "validate": False,
                }
            )
        )

        mock_jira.issue.assert_not_called()

    def test_invalid_issue_key_format(self, tool: FormatCommitTool) -> None:
        """Test error for invalid issue key format."""
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(tool.execute({"issueKey": "invalid", "message": "Add feature"}))

        assert "Invalid issue key format" in str(exc_info.value)

    def test_issue_not_found(self, tool: FormatCommitTool, mock_jira: Mock) -> None:
        """Test error when issue not found."""
        mock_jira.issue.side_effect = Exception("Issue not found")

        with pytest.raises(ValueError) as exc_info:
            asyncio.run(tool.execute({"issueKey": "PROJ-999", "message": "Add feature"}))

        assert "not found" in str(exc_info.value)

    def test_requires_issue_key(self, tool: FormatCommitTool) -> None:
        """Test that issueKey is required."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({"message": "Add feature"}))

    def test_requires_message(self, tool: FormatCommitTool) -> None:
        """Test that message is required."""
        with pytest.raises(ValueError, match="message is required"):
            asyncio.run(tool.execute({"issueKey": "PROJ-123"}))

    def test_tool_definition(self, tool: FormatCommitTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "format_commit"
        assert "issueKey" in definition.inputSchema["properties"]
        assert "message" in definition.inputSchema["properties"]
        assert "type" in definition.inputSchema["properties"]

