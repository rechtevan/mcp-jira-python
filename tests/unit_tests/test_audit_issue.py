"""Unit tests for AuditIssueTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.audit_issue import AuditIssueTool


@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock issue with common fields."""
    issue = Mock()
    issue.key = "PROJ-123"
    issue.fields.summary = "Test issue"
    issue.fields.description = (
        "This is a test issue.\n\n"
        "## Acceptance Criteria\n"
        "- Given a user is logged in\n"
        "- When they click the button\n"
        "- Then the action completes\n\n"
        "## Definition of Done\n"
        "- [ ] Code reviewed\n"
        "- [ ] Tests passing\n"
    )
    issue.fields.issuetype = Mock(__str__=lambda s: "Story")
    issue.fields.priority = Mock(__str__=lambda s: "Medium")
    issue.fields.assignee = Mock(displayName="John Doe")
    issue.fields.labels = ["feature", "backend"]
    issue.fields.components = []
    # Story points custom field
    issue.fields.customfield_10016 = 5
    # Epic link custom field
    issue.fields.customfield_10014 = Mock(key="PROJ-100")
    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> AuditIssueTool:
    """Create tool with mock Jira."""
    tool = AuditIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestAuditIssueTool:
    """Tests for AuditIssueTool."""

    def test_execute_high_quality_issue(self, tool: AuditIssueTool, mock_jira: Mock) -> None:
        """Test auditing a high-quality issue."""
        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))

        assert result[0].type == "text"
        data = json.loads(result[0].text)

        assert data["issueKey"] == "PROJ-123"
        assert data["qualityScore"] >= 75
        assert data["qualityLevel"] in ("Excellent", "Good")
        assert "metadata" in data

    def test_execute_missing_description(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test auditing issue with no description."""
        mock_issue.fields.description = None

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert "No description provided" in data["issues"]
        assert data["qualityScore"] < 90

    def test_execute_short_description(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test auditing issue with short description."""
        mock_issue.fields.description = "Fix bug"

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert "Description is very short" in data["issues"]

    def test_execute_no_acceptance_criteria(self, tool: AuditIssueTool, mock_jira: Mock) -> None:
        """Test auditing issue without acceptance criteria."""
        # Create a new mock issue without AC (no AC keywords in description)
        issue_no_ac = Mock()
        issue_no_ac.key = "PROJ-123"
        issue_no_ac.fields.summary = "Test issue"
        issue_no_ac.fields.description = (
            "This is a longer description that explains what needs to be done "
            "for this feature but lacks proper documentation."
        )
        issue_no_ac.fields.issuetype = Mock(__str__=lambda s: "Story")
        issue_no_ac.fields.priority = Mock(__str__=lambda s: "Medium")
        issue_no_ac.fields.assignee = Mock(displayName="John Doe")
        issue_no_ac.fields.labels = ["feature"]
        issue_no_ac.fields.components = []
        issue_no_ac.fields.customfield_10016 = 5
        issue_no_ac.fields.customfield_10014 = Mock(key="PROJ-100")
        mock_jira.issue.return_value = issue_no_ac

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert "No acceptance criteria found" in data["issues"]

    def test_execute_no_story_points(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test auditing issue without story points."""
        mock_issue.fields.customfield_10016 = None
        mock_issue.fields.customfield_10026 = None
        delattr(mock_issue.fields, "story_points")

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert "No story points assigned" in data["issues"]

    def test_execute_no_priority(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test auditing issue without priority."""
        mock_issue.fields.priority = None

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert "No priority set" in data["issues"]

    def test_execute_no_assignee(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test auditing issue without assignee."""
        mock_issue.fields.assignee = None

        result = asyncio.run(tool.execute({"issueKey": "PROJ-123"}))
        data = json.loads(result[0].text)

        assert any("Assign" in s for s in data["suggestions"])

    def test_execute_skip_ac_check(
        self, tool: AuditIssueTool, mock_jira: Mock, mock_issue: Mock
    ) -> None:
        """Test skipping acceptance criteria check."""
        mock_issue.fields.description = "Simple description without AC"

        result = asyncio.run(
            tool.execute(
                {
                    "issueKey": "PROJ-123",
                    "checkAcceptanceCriteria": False,
                }
            )
        )
        data = json.loads(result[0].text)

        assert "No acceptance criteria found" not in data["issues"]

    def test_execute_missing_issue_key(self, tool: AuditIssueTool) -> None:
        """Test error when issueKey missing."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({}))

    def test_execute_api_error(self, tool: AuditIssueTool, mock_jira: Mock) -> None:
        """Test error handling for API errors."""
        mock_jira.issue.side_effect = Exception("API error")

        with pytest.raises(Exception, match="Failed to audit issue"):
            asyncio.run(tool.execute({"issueKey": "PROJ-123"}))

    def test_tool_definition(self, tool: AuditIssueTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "audit_issue"
        assert "issueKey" in definition.inputSchema["properties"]
        assert definition.inputSchema["required"] == ["issueKey"]
