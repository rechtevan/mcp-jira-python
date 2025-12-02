"""Unit tests for the GetFieldMappingTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_field_mapping import GetFieldMappingTool


@pytest.fixture
def mock_jira_fields() -> list[dict]:
    """Sample field data mimicking Jira API response."""
    return [
        {
            "id": "summary",
            "name": "Summary",
            "custom": False,
            "schema": {"type": "string"},
        },
        {
            "id": "description",
            "name": "Description",
            "custom": False,
            "schema": {"type": "string"},
        },
        {
            "id": "customfield_10001",
            "name": "Story Points",
            "custom": True,
            "schema": {"type": "number"},
        },
        {
            "id": "customfield_10002",
            "name": "Sprint",
            "custom": True,
            "schema": {"type": "array"},
        },
    ]


@pytest.fixture
def mock_jira(mock_jira_fields: list[dict]) -> Mock:
    """Mock Jira client with field data."""
    jira = Mock()
    jira.fields.return_value = mock_jira_fields
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetFieldMappingTool:
    """Create tool with mock Jira client."""
    tool = GetFieldMappingTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetFieldMappingTool:
    """Tests for GetFieldMappingTool."""

    def test_tool_definition(self, tool: GetFieldMappingTool) -> None:
        """Test that tool definition is correct."""
        definition = tool.get_tool_definition()
        assert definition.name == "get_field_mapping"
        assert "field" in definition.description.lower()

    def test_execute_returns_all_fields(self, tool: GetFieldMappingTool) -> None:
        """Test that execute returns all fields by default."""
        result = asyncio.run(tool.execute({}))

        assert len(result) == 1
        data = json.loads(result[0].text)

        assert data["count"] == 4
        assert data["totalAvailable"] == 4
        assert len(data["fields"]) == 4

    def test_execute_custom_only(self, tool: GetFieldMappingTool) -> None:
        """Test filtering to custom fields only."""
        result = asyncio.run(tool.execute({"customOnly": True}))

        data = json.loads(result[0].text)

        assert data["count"] == 2
        for field in data["fields"]:
            assert field["custom"] is True

    def test_execute_search_filter(self, tool: GetFieldMappingTool) -> None:
        """Test search filter."""
        result = asyncio.run(tool.execute({"search": "point"}))

        data = json.loads(result[0].text)

        assert data["count"] == 1
        assert data["fields"][0]["name"] == "Story Points"

    def test_execute_search_case_insensitive(self, tool: GetFieldMappingTool) -> None:
        """Test that search is case-insensitive."""
        result = asyncio.run(tool.execute({"search": "SPRINT"}))

        data = json.loads(result[0].text)

        assert data["count"] == 1
        assert data["fields"][0]["name"] == "Sprint"

    def test_execute_limit(self, tool: GetFieldMappingTool) -> None:
        """Test result limiting."""
        result = asyncio.run(tool.execute({"limit": 2}))

        data = json.loads(result[0].text)

        assert data["count"] == 2
        assert data["totalAvailable"] == 4

    def test_execute_combined_filters(self, tool: GetFieldMappingTool) -> None:
        """Test combining multiple filters."""
        result = asyncio.run(
            tool.execute(
                {
                    "customOnly": True,
                    "search": "s",  # Matches "Story Points" and "Sprint"
                    "limit": 1,
                }
            )
        )

        data = json.loads(result[0].text)

        assert data["count"] == 1
        assert data["fields"][0]["custom"] is True

    def test_field_structure(self, tool: GetFieldMappingTool) -> None:
        """Test that returned fields have correct structure."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        field = data["fields"][0]

        assert "name" in field
        assert "id" in field
        assert "custom" in field
        assert "type" in field

