"""Unit tests for GetCreateMetaTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_create_meta import GetCreateMetaTool


@pytest.fixture
def mock_create_meta() -> dict:
    """Sample create metadata response."""
    return {
        "projects": [
            {
                "key": "PROJ",
                "name": "Test Project",
                "issuetypes": [
                    {
                        "name": "Story",
                        "description": "A user story",
                        "fields": {
                            "summary": {
                                "name": "Summary",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                            "description": {
                                "name": "Description",
                                "required": False,
                                "schema": {"type": "string"},
                            },
                            "priority": {
                                "name": "Priority",
                                "required": True,
                                "schema": {"type": "priority"},
                                "allowedValues": [
                                    {"name": "High"},
                                    {"name": "Medium"},
                                    {"name": "Low"},
                                ],
                            },
                            "customfield_10001": {
                                "name": "Story Points",
                                "required": False,
                                "schema": {"type": "number"},
                            },
                            "project": {"name": "Project", "required": True},
                            "issuetype": {"name": "Issue Type", "required": True},
                        },
                    },
                    {
                        "name": "Bug",
                        "description": "A defect",
                        "fields": {
                            "summary": {
                                "name": "Summary",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                            "description": {
                                "name": "Description",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                        },
                    },
                ],
            }
        ]
    }


@pytest.fixture
def mock_fields() -> list[dict]:
    """Sample field data."""
    return [
        {"id": "summary", "name": "Summary", "custom": False},
        {"id": "customfield_10001", "name": "Story Points", "custom": True},
    ]


@pytest.fixture
def mock_jira(mock_create_meta: dict, mock_fields: list[dict]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.createmeta.return_value = mock_create_meta
    jira.fields.return_value = mock_fields
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetCreateMetaTool:
    """Create tool with mock Jira."""
    tool = GetCreateMetaTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetCreateMeta:
    """Tests for GetCreateMetaTool."""

    def test_returns_issue_types(self, tool: GetCreateMetaTool) -> None:
        """Test that issue types are returned."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        assert data["projectKey"] == "PROJ"
        assert len(data["issueTypes"]) == 2
        assert data["issueTypes"][0]["name"] == "Story"
        assert data["issueTypes"][1]["name"] == "Bug"

    def test_returns_required_fields(self, tool: GetCreateMetaTool) -> None:
        """Test that required fields are identified."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        story = data["issueTypes"][0]

        required_names = [f["name"] for f in story["requiredFields"]]
        assert "Summary" in required_names
        assert "Priority" in required_names

    def test_excludes_project_and_issuetype(self, tool: GetCreateMetaTool) -> None:
        """Test that project and issuetype fields are excluded."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        story = data["issueTypes"][0]

        all_field_ids = [f["id"] for f in story["requiredFields"]]
        all_field_ids += [f["id"] for f in story["optionalFields"]]

        assert "project" not in all_field_ids
        assert "issuetype" not in all_field_ids

    def test_includes_allowed_values(self, tool: GetCreateMetaTool) -> None:
        """Test that allowed values are included for select fields."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ"}))

        data = json.loads(result[0].text)
        story = data["issueTypes"][0]

        priority_field = next(f for f in story["requiredFields"] if f["name"] == "Priority")
        assert "allowedValues" in priority_field
        assert "High" in priority_field["allowedValues"]

    def test_filter_by_issue_type(self, tool: GetCreateMetaTool) -> None:
        """Test filtering to specific issue type."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Bug"}))

        data = json.loads(result[0].text)
        assert len(data["issueTypes"]) == 1
        assert data["issueTypes"][0]["name"] == "Bug"

    def test_filter_case_insensitive(self, tool: GetCreateMetaTool) -> None:
        """Test that issue type filter is case-insensitive."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "story"}))

        data = json.loads(result[0].text)
        assert len(data["issueTypes"]) == 1
        assert data["issueTypes"][0]["name"] == "Story"

    def test_invalid_issue_type_error(self, tool: GetCreateMetaTool) -> None:
        """Test error for invalid issue type."""
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Invalid"}))

        error = str(exc_info.value)
        assert "Invalid" in error
        assert "Available" in error

    def test_requires_project_key(self, tool: GetCreateMetaTool) -> None:
        """Test that projectKey is required."""
        with pytest.raises(ValueError, match="projectKey is required"):
            asyncio.run(tool.execute({}))

    def test_tool_definition(self, tool: GetCreateMetaTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "get_create_meta"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "issueType" in definition.inputSchema["properties"]

