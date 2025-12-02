"""Unit tests for GetIssueTool custom field functionality."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_issue import GetIssueTool


@pytest.fixture
def mock_fields() -> list[dict]:
    """Sample field data for the field mapper."""
    return [
        {"id": "summary", "name": "Summary", "custom": False},
        {"id": "description", "name": "Description", "custom": False},
        {"id": "customfield_10001", "name": "Story Points", "custom": True},
        {"id": "customfield_10002", "name": "Sprint", "custom": True},
        {"id": "customfield_10003", "name": "Epic Link", "custom": True},
        {"id": "customfield_10004", "name": "Team", "custom": True},
    ]


@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock issue with custom fields."""
    issue = Mock()
    issue.key = "TEST-123"
    issue.fields = Mock()
    issue.fields.summary = "Test Issue"
    issue.fields.description = "Test Description"
    issue.fields.status = Mock()
    issue.fields.status.__str__ = lambda self: "Open"
    issue.fields.priority = Mock()
    issue.fields.priority.__str__ = lambda self: "High"
    issue.fields.assignee = Mock()
    issue.fields.assignee.__str__ = lambda self: "Test User"
    issue.fields.issuetype = Mock()
    issue.fields.issuetype.__str__ = lambda self: "Task"

    # Comments
    mock_comment = Mock()
    mock_comment.id = "10001"
    mock_comment.author = Mock()
    mock_comment.author.__str__ = lambda self: "Author"
    mock_comment.body = "Test comment"
    mock_comment.created = "2024-01-01T00:00:00.000+0000"
    issue.fields.comment = Mock()
    issue.fields.comment.comments = [mock_comment]

    # Attachments
    issue.fields.attachment = []

    # Raw fields with custom field values
    issue.raw = {
        "fields": {
            "summary": "Test Issue",
            "customfield_10001": 5,  # Story Points
            "customfield_10002": [  # Sprint (array)
                {"name": "Sprint 10"},
                {"name": "Sprint 11"},
            ],
            "customfield_10003": "EPIC-1",  # Epic Link (string)
            "customfield_10004": {"value": "Platform Team"},  # Team (select)
            "customfield_99999": None,  # Should be skipped
        }
    }

    return issue


@pytest.fixture
def mock_jira(mock_issue: Mock, mock_fields: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.issue.return_value = mock_issue
    jira.fields.return_value = mock_fields
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetIssueTool:
    """Create tool with mock Jira."""
    tool = GetIssueTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetIssueCustomFields:
    """Tests for custom field functionality in GetIssueTool."""

    def test_includes_custom_fields_by_default(self, tool: GetIssueTool) -> None:
        """Test that custom fields are included by default."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        assert "customFields" in data
        assert "Story Points" in data["customFields"]
        assert data["customFields"]["Story Points"] == 5

    def test_custom_fields_have_friendly_names(self, tool: GetIssueTool) -> None:
        """Test that custom field names are human-readable."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        custom_fields = data["customFields"]

        # Should have friendly names, not IDs
        assert "Story Points" in custom_fields
        assert "Sprint" in custom_fields
        assert "Epic Link" in custom_fields
        assert "Team" in custom_fields

        # Should NOT have raw IDs
        assert "customfield_10001" not in custom_fields

    def test_formats_array_fields(self, tool: GetIssueTool) -> None:
        """Test that array fields are formatted correctly."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        sprints = data["customFields"]["Sprint"]

        assert isinstance(sprints, list)
        assert "Sprint 10" in sprints
        assert "Sprint 11" in sprints

    def test_formats_select_fields(self, tool: GetIssueTool) -> None:
        """Test that select fields extract the value."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        assert data["customFields"]["Team"] == "Platform Team"

    def test_skips_null_custom_fields(self, tool: GetIssueTool) -> None:
        """Test that null custom fields are not included."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        # customfield_99999 was null, should not appear
        assert "customfield_99999" not in str(data)

    def test_exclude_custom_fields(self, tool: GetIssueTool) -> None:
        """Test excluding custom fields from response."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "includeCustomFields": False}))

        data = json.loads(result[0].text)
        assert "customFields" not in data
        assert "summary" in data  # Standard fields still present

    def test_custom_fields_only(self, tool: GetIssueTool) -> None:
        """Test returning only custom fields."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123", "customFieldsOnly": True}))

        data = json.loads(result[0].text)
        assert "customFields" in data
        assert "key" in data
        # Standard fields should not be present
        assert "summary" not in data
        assert "description" not in data
        assert "comments" not in data

    def test_standard_fields_still_present(self, tool: GetIssueTool) -> None:
        """Test that standard fields are still returned."""
        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        data = json.loads(result[0].text)
        assert data["key"] == "TEST-123"
        assert data["summary"] == "Test Issue"
        assert data["status"] == "Open"
        assert "comments" in data


@pytest.mark.unit
class TestFormatFieldValue:
    """Tests for field value formatting."""

    def test_format_none(self, tool: GetIssueTool) -> None:
        """Test formatting None value."""
        assert tool._format_field_value(None) is None

    def test_format_primitive(self, tool: GetIssueTool) -> None:
        """Test formatting primitive values."""
        assert tool._format_field_value(5) == 5
        assert tool._format_field_value("test") == "test"
        assert tool._format_field_value(True) is True

    def test_format_object_with_display_name(self, tool: GetIssueTool) -> None:
        """Test formatting object with displayName."""
        obj = Mock()
        obj.displayName = "Test User"
        assert tool._format_field_value(obj) == "Test User"

    def test_format_object_with_name(self, tool: GetIssueTool) -> None:
        """Test formatting object with name."""
        obj = Mock(spec=["name"])
        obj.name = "Test Status"
        assert tool._format_field_value(obj) == "Test Status"

    def test_format_object_with_value(self, tool: GetIssueTool) -> None:
        """Test formatting object with value."""
        obj = Mock(spec=["value"])
        obj.value = "Option A"
        assert tool._format_field_value(obj) == "Option A"

    def test_format_dict_with_name(self, tool: GetIssueTool) -> None:
        """Test formatting dict with name key."""
        assert tool._format_field_value({"name": "Test"}) == "Test"

    def test_format_dict_with_value(self, tool: GetIssueTool) -> None:
        """Test formatting dict with value key."""
        assert tool._format_field_value({"value": "Test"}) == "Test"

    def test_format_list(self, tool: GetIssueTool) -> None:
        """Test formatting list of values."""
        result = tool._format_field_value([{"name": "A"}, {"name": "B"}])
        assert result == ["A", "B"]


