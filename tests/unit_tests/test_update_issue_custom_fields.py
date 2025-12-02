"""Unit tests for UpdateIssueTool custom field functionality."""

import asyncio
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.update_issue import UpdateIssueTool


@pytest.fixture
def mock_fields() -> list[dict]:
    """Sample field data for the field mapper."""
    return [
        {"id": "summary", "name": "Summary", "custom": False},
        {"id": "customfield_10001", "name": "Story Points", "custom": True},
        {"id": "customfield_10002", "name": "Sprint", "custom": True},
        {"id": "customfield_10003", "name": "Team", "custom": True},
    ]


@pytest.fixture
def mock_issue() -> Mock:
    """Mock issue for update."""
    issue = Mock()
    issue.key = "TEST-123"
    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock, mock_fields: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    jira.fields.return_value = mock_fields
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> UpdateIssueTool:
    """Create tool with mock Jira."""
    tool = UpdateIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestUpdateIssueCustomFields:
    """Tests for custom field support in UpdateIssueTool."""

    def test_update_with_custom_fields_by_name(
        self, tool: UpdateIssueTool, mock_issue: Mock
    ) -> None:
        """Test updating issue with custom fields using friendly names."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "customFields": {
                        "Story Points": 8,
                        "Team": "Platform",
                    },
                }
            )
        )

        # Verify update was called with translated field IDs
        call_args = mock_issue.update.call_args
        fields = call_args.kwargs["fields"]

        assert fields["customfield_10001"] == 8
        assert fields["customfield_10003"] == "Platform"

    def test_update_with_custom_fields_by_id(self, tool: UpdateIssueTool, mock_issue: Mock) -> None:
        """Test updating issue with custom fields using IDs directly."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "customFields": {
                        "customfield_10001": 13,
                    },
                }
            )
        )

        call_args = mock_issue.update.call_args
        fields = call_args.kwargs["fields"]

        assert fields["customfield_10001"] == 13

    def test_update_with_mixed_standard_and_custom(
        self, tool: UpdateIssueTool, mock_issue: Mock
    ) -> None:
        """Test updating issue with both standard and custom fields."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "summary": "Updated Summary",
                    "priority": "High",
                    "customFields": {
                        "Story Points": 5,
                    },
                }
            )
        )

        call_args = mock_issue.update.call_args
        fields = call_args.kwargs["fields"]

        # Standard fields
        assert fields["summary"] == "Updated Summary"
        assert fields["priority"] == {"name": "High"}

        # Custom fields
        assert fields["customfield_10001"] == 5

    def test_update_without_custom_fields(self, tool: UpdateIssueTool, mock_issue: Mock) -> None:
        """Test that updating without custom fields still works."""
        _ = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "summary": "Updated Summary",
                }
            )
        )

        call_args = mock_issue.update.call_args
        fields = call_args.kwargs["fields"]

        assert fields["summary"] == "Updated Summary"
        assert "customfield_10001" not in fields

    def test_update_returns_success_message(self, tool: UpdateIssueTool) -> None:
        """Test that response includes success message."""
        result = asyncio.run(
            tool.execute(
                {
                    "issueKey": "TEST-123",
                    "summary": "Updated",
                }
            )
        )

        assert "updated successfully" in result[0].text
        assert "TEST-123" in result[0].text

    def test_update_requires_issue_key(self, tool: UpdateIssueTool) -> None:
        """Test that issueKey is required."""
        with pytest.raises(ValueError, match="issueKey is required"):
            asyncio.run(tool.execute({}))
