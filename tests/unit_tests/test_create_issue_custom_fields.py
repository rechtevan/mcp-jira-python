"""Unit tests for CreateIssueTool custom field functionality."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.create_issue import CreateIssueTool


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
def mock_created_issue() -> Mock:
    """Mock created issue response."""
    issue = Mock()
    issue.key = "TEST-123"
    issue.id = "12345"
    issue.self = "https://jira.example.com/rest/api/2/issue/12345"
    return issue


@pytest.fixture
def mock_jira(mock_created_issue: Mock, mock_fields: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.create_issue.return_value = mock_created_issue
    jira.fields.return_value = mock_fields
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> CreateIssueTool:
    """Create tool with mock Jira."""
    tool = CreateIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestCreateIssueCustomFields:
    """Tests for custom field support in CreateIssueTool."""

    def test_create_with_custom_fields_by_name(
        self, tool: CreateIssueTool, mock_jira: Mock
    ) -> None:
        """Test creating issue with custom fields using friendly names."""
        _ = asyncio.run(
            tool.execute(
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue",
                    "issueType": "Task",
                    "customFields": {
                        "Story Points": 5,
                        "Team": "Platform",
                    },
                }
            )
        )

        # Verify the API was called with translated field IDs
        call_args = mock_jira.create_issue.call_args
        fields = call_args.kwargs["fields"]

        assert fields["customfield_10001"] == 5
        assert fields["customfield_10003"] == "Platform"

    def test_create_with_custom_fields_by_id(self, tool: CreateIssueTool, mock_jira: Mock) -> None:
        """Test creating issue with custom fields using IDs directly."""
        _ = asyncio.run(
            tool.execute(
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue",
                    "issueType": "Task",
                    "customFields": {
                        "customfield_10001": 8,
                    },
                }
            )
        )

        call_args = mock_jira.create_issue.call_args
        fields = call_args.kwargs["fields"]

        # Should pass through the ID directly
        assert fields["customfield_10001"] == 8

    def test_create_with_mixed_standard_and_custom(
        self, tool: CreateIssueTool, mock_jira: Mock
    ) -> None:
        """Test creating issue with both standard and custom fields."""
        _ = asyncio.run(
            tool.execute(
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue",
                    "issueType": "Task",
                    "description": "Test description",
                    "priority": "High",
                    "customFields": {
                        "Story Points": 3,
                    },
                }
            )
        )

        call_args = mock_jira.create_issue.call_args
        fields = call_args.kwargs["fields"]

        # Standard fields
        assert fields["summary"] == "Test Issue"
        assert fields["description"] == "Test description"
        assert fields["priority"] == {"name": "High"}

        # Custom fields
        assert fields["customfield_10001"] == 3

    def test_create_without_custom_fields(self, tool: CreateIssueTool, mock_jira: Mock) -> None:
        """Test that creating issue without custom fields still works."""
        _ = asyncio.run(
            tool.execute(
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue",
                    "issueType": "Task",
                }
            )
        )

        call_args = mock_jira.create_issue.call_args
        fields = call_args.kwargs["fields"]

        # Should have standard fields only
        assert "customfield_10001" not in fields
        assert fields["summary"] == "Test Issue"

    def test_create_returns_issue_key(self, tool: CreateIssueTool) -> None:
        """Test that response includes issue key."""
        result = asyncio.run(
            tool.execute(
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue",
                    "issueType": "Task",
                }
            )
        )

        data = json.loads(result[0].text)
        assert data["key"] == "TEST-123"
        assert data["id"] == "12345"
