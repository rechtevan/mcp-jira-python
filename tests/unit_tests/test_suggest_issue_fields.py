"""Unit tests for SuggestIssueFieldsTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.suggest_issue_fields import SuggestIssueFieldsTool


@pytest.fixture
def mock_create_meta() -> dict:
    """Sample create metadata."""
    return {
        "projects": [
            {
                "key": "PROJ",
                "name": "Test Project",
                "issuetypes": [
                    {
                        "name": "Story",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                            "description": {"name": "Description", "required": False},
                            "priority": {
                                "name": "Priority",
                                "required": True,
                                "allowedValues": [
                                    {"name": "High"},
                                    {"name": "Medium"},
                                    {"name": "Low"},
                                ],
                            },
                            "project": {"name": "Project", "required": True},
                            "issuetype": {"name": "Issue Type", "required": True},
                        },
                    },
                    {
                        "name": "Bug",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                        },
                    },
                ],
            }
        ]
    }


@pytest.fixture
def mock_epics() -> list[Mock]:
    """Sample epics."""
    epics = []
    for key, summary in [("PROJ-10", "Auth Epic"), ("PROJ-20", "UI Epic")]:
        epic = Mock()
        epic.key = key
        epic.fields = Mock()
        epic.fields.summary = summary
        epics.append(epic)
    return epics


@pytest.fixture
def mock_jira(mock_create_meta: dict, mock_epics: list[Mock]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.createmeta.return_value = mock_create_meta
    jira.search_issues.return_value = mock_epics
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> SuggestIssueFieldsTool:
    """Create tool with mock Jira."""
    tool = SuggestIssueFieldsTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestSuggestIssueFields:
    """Tests for SuggestIssueFieldsTool."""

    def test_returns_required_fields(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that required fields are returned."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Story"})
        )

        data = json.loads(result[0].text)
        assert "requiredFields" in data
        required_names = [f["name"] for f in data["requiredFields"]]
        assert "Summary" in required_names
        assert "Priority" in required_names

    def test_excludes_project_and_issuetype(
        self, tool: SuggestIssueFieldsTool
    ) -> None:
        """Test that project and issuetype fields are excluded."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Story"})
        )

        data = json.loads(result[0].text)
        field_ids = [f["id"] for f in data["requiredFields"]]
        assert "project" not in field_ids
        assert "issuetype" not in field_ids

    def test_story_recommendations(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that Story type gets story-specific recommendations."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Story"})
        )

        data = json.loads(result[0].text)
        rec_fields = [r["field"] for r in data["recommendations"]]
        assert "Story Points" in rec_fields
        assert "Epic Link" in rec_fields

    def test_bug_recommendations(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that Bug type gets bug-specific recommendations."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Bug"})
        )

        data = json.loads(result[0].text)
        rec_fields = [r["field"] for r in data["recommendations"]]
        assert "Priority" in rec_fields

    def test_includes_available_epics(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that available epics are included for non-epic types."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Story"})
        )

        data = json.loads(result[0].text)
        assert "availableEpics" in data
        assert len(data["availableEpics"]) == 2
        assert data["availableEpics"][0]["key"] == "PROJ-10"

    def test_case_insensitive_issue_type(
        self, tool: SuggestIssueFieldsTool
    ) -> None:
        """Test that issue type matching is case-insensitive."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "story"})
        )

        data = json.loads(result[0].text)
        assert "requiredFields" in data

    def test_invalid_issue_type_error(self, tool: SuggestIssueFieldsTool) -> None:
        """Test error for invalid issue type."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Invalid"})
        )

        data = json.loads(result[0].text)
        assert "error" in data
        assert "availableTypes" in data

    def test_requires_project_key(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that projectKey is required."""
        with pytest.raises(ValueError, match="projectKey is required"):
            asyncio.run(tool.execute({"issueType": "Story"}))

    def test_requires_issue_type(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that issueType is required."""
        with pytest.raises(ValueError, match="issueType is required"):
            asyncio.run(tool.execute({"projectKey": "PROJ"}))

    def test_includes_tips(self, tool: SuggestIssueFieldsTool) -> None:
        """Test that helpful tips are included."""
        result = asyncio.run(
            tool.execute({"projectKey": "PROJ", "issueType": "Story"})
        )

        data = json.loads(result[0].text)
        assert "tips" in data
        assert len(data["tips"]) > 0

    def test_tool_definition(self, tool: SuggestIssueFieldsTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "suggest_issue_fields"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "issueType" in definition.inputSchema["properties"]

