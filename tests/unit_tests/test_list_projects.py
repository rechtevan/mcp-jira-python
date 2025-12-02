"""Unit tests for ListProjectsTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.list_projects import ListProjectsTool


@pytest.fixture
def mock_projects() -> list[Mock]:
    """Sample projects."""
    projects = []
    for key, name, lead in [
        ("PROJ", "Test Project", "lead@example.com"),
        ("DEV", "Development", "dev@example.com"),
        ("QA", "Quality Assurance", "qa@example.com"),
    ]:
        project = Mock()
        project.key = key
        project.name = name
        project.lead = Mock()
        project.lead.__str__ = lambda self, lead_email=lead: lead_email
        project.projectTypeKey = "software"
        projects.append(project)
    return projects


@pytest.fixture
def mock_jira(mock_projects: list[Mock]) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.projects.return_value = mock_projects
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> ListProjectsTool:
    """Create tool with mock Jira."""
    tool = ListProjectsTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestListProjects:
    """Tests for ListProjectsTool."""

    def test_returns_projects(self, tool: ListProjectsTool) -> None:
        """Test that projects are returned."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        assert data["count"] == 3
        assert len(data["projects"]) == 3

    def test_project_includes_key_and_name(self, tool: ListProjectsTool) -> None:
        """Test that projects include key and name."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        project = data["projects"][0]
        assert project["key"] == "PROJ"
        assert project["name"] == "Test Project"
        assert project["lead"] == "lead@example.com"

    def test_filter_by_query(self, tool: ListProjectsTool) -> None:
        """Test filtering projects by query."""
        result = asyncio.run(tool.execute({"query": "dev"}))

        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["projects"][0]["key"] == "DEV"
        assert data["filter"] == "dev"

    def test_filter_case_insensitive(self, tool: ListProjectsTool) -> None:
        """Test that filter is case-insensitive."""
        result = asyncio.run(tool.execute({"query": "QUALITY"}))

        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["projects"][0]["key"] == "QA"

    def test_filter_by_key(self, tool: ListProjectsTool) -> None:
        """Test filtering by project key."""
        result = asyncio.run(tool.execute({"query": "proj"}))

        data = json.loads(result[0].text)
        assert data["count"] == 1
        assert data["projects"][0]["key"] == "PROJ"

    def test_respects_max_results(self, tool: ListProjectsTool) -> None:
        """Test that maxResults is respected."""
        result = asyncio.run(tool.execute({"maxResults": 2}))

        data = json.loads(result[0].text)
        assert data["count"] == 2

    def test_no_filter_returns_all(self, tool: ListProjectsTool) -> None:
        """Test that no filter returns all projects."""
        result = asyncio.run(tool.execute({}))

        data = json.loads(result[0].text)
        assert "filter" not in data

    def test_tool_definition(self, tool: ListProjectsTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "list_projects"
        assert "query" in definition.inputSchema["properties"]
        assert "maxResults" in definition.inputSchema["properties"]
        assert definition.inputSchema["required"] == []
