"""Unit tests for SuggestIssueFieldsTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.suggest_issue_fields import SuggestIssueFieldsTool


@pytest.fixture
def mock_createmeta() -> dict:
    """Create mock createmeta response."""
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
                                "required": False,
                                "allowedValues": [
                                    {"name": "High"},
                                    {"name": "Medium"},
                                    {"name": "Low"},
                                ],
                            },
                        },
                    },
                    {
                        "name": "Bug",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                        },
                    },
                    {
                        "name": "Task",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                        },
                    },
                    {
                        "name": "Epic",
                        "fields": {
                            "summary": {"name": "Summary", "required": True},
                        },
                    },
                ],
            }
        ]
    }


@pytest.fixture
def mock_epic() -> Mock:
    """Create mock epic."""
    epic = Mock()
    epic.key = "PROJ-100"
    epic.fields.summary = "Epic summary"
    return epic


@pytest.fixture
def mock_jira(mock_createmeta: dict, mock_epic: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.createmeta.return_value = mock_createmeta
    jira.search_issues.return_value = [mock_epic]
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> SuggestIssueFieldsTool:
    """Create tool with mock Jira."""
    tool = SuggestIssueFieldsTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestSuggestIssueFieldsTool:
    """Tests for SuggestIssueFieldsTool."""

    def test_execute_story(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test suggestions for Story issue type."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Story"}))

        assert result[0].type == "text"
        data = json.loads(result[0].text)

        assert data["projectKey"] == "PROJ"
        assert data["issueType"] == "Story"
        assert len(data["requiredFields"]) > 0
        assert any(r["field"] == "Story Points" for r in data["recommendations"])
        assert any(r["field"] == "Epic Link" for r in data["recommendations"])
        assert "availableEpics" in data
        assert data["availableEpics"][0]["key"] == "PROJ-100"

    def test_execute_bug(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test suggestions for Bug issue type."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Bug"}))

        data = json.loads(result[0].text)
        assert data["issueType"] == "Bug"
        assert any(r["field"] == "Priority" for r in data["recommendations"])
        assert any("Steps to Reproduce" in r["field"] for r in data["recommendations"])

    def test_execute_task(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test suggestions for Task issue type."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Task"}))

        data = json.loads(result[0].text)
        assert data["issueType"] == "Task"
        assert any(r["field"] == "Story Points" for r in data["recommendations"])

    def test_execute_epic(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test suggestions for Epic issue type."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Epic"}))

        data = json.loads(result[0].text)
        assert data["issueType"] == "Epic"
        assert any(r["field"] == "Epic Name" for r in data["recommendations"])
        # Epics shouldn't have availableEpics
        assert "availableEpics" not in data

    def test_execute_unknown_issue_type(
        self, tool: SuggestIssueFieldsTool, mock_jira: Mock
    ) -> None:
        """Test error when issue type not found."""
        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Unknown"}))

        data = json.loads(result[0].text)
        assert "error" in data
        assert "availableTypes" in data

    def test_execute_project_not_found(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test error when project not found."""
        mock_jira.createmeta.return_value = {"projects": []}

        with pytest.raises(ValueError, match="not found"):
            asyncio.run(tool.execute({"projectKey": "NONEXIST", "issueType": "Story"}))

    def test_execute_missing_project_key(self, tool: SuggestIssueFieldsTool) -> None:
        """Test error when projectKey missing."""
        with pytest.raises(ValueError, match="projectKey is required"):
            asyncio.run(tool.execute({"issueType": "Story"}))

    def test_execute_missing_issue_type(self, tool: SuggestIssueFieldsTool) -> None:
        """Test error when issueType missing."""
        with pytest.raises(ValueError, match="issueType is required"):
            asyncio.run(tool.execute({"projectKey": "PROJ"}))

    def test_execute_api_error(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test error handling for API errors."""
        mock_jira.createmeta.side_effect = Exception("API error")

        with pytest.raises(Exception, match="Failed to get suggestions"):
            asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Story"}))

    def test_execute_epic_search_error(self, tool: SuggestIssueFieldsTool, mock_jira: Mock) -> None:
        """Test that epic search errors are handled gracefully."""
        mock_jira.search_issues.side_effect = Exception("Epic search failed")

        result = asyncio.run(tool.execute({"projectKey": "PROJ", "issueType": "Story"}))

        data = json.loads(result[0].text)
        # Should succeed without epics
        assert "availableEpics" not in data

    def test_tool_definition(self, tool: SuggestIssueFieldsTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "suggest_issue_fields"
        assert "projectKey" in definition.inputSchema["properties"]
        assert "issueType" in definition.inputSchema["properties"]
        assert definition.inputSchema["required"] == ["projectKey", "issueType"]
