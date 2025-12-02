"""Unit tests for CreateIssueLinkTool."""

import asyncio
import json
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.create_issue_link import CreateIssueLinkTool


@pytest.fixture
def mock_jira() -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.create_issue_link.return_value = None
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> CreateIssueLinkTool:
    """Create tool with mock Jira."""
    tool = CreateIssueLinkTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestCreateIssueLinkTool:
    """Tests for CreateIssueLinkTool."""

    def test_execute_creates_link(
        self, tool: CreateIssueLinkTool, mock_jira: Mock
    ) -> None:
        """Test creating an issue link."""
        result = asyncio.run(
            tool.execute({
                "inwardIssueKey": "TEST-123",
                "outwardIssueKey": "TEST-456",
                "linkType": "Relates",
            })
        )

        data = json.loads(result[0].text)
        assert result[0].type == "text"
        assert data["inwardIssue"].upper() == "TEST-123"
        assert data["outwardIssue"].upper() == "TEST-456"
        assert data["linkType"].upper() == "RELATES"

        mock_jira.create_issue_link.assert_called_once_with(
            type="Relates",
            inwardIssue="TEST-123",
            outwardIssue="TEST-456",
        )

    def test_requires_inward_issue(self, tool: CreateIssueLinkTool) -> None:
        """Test that inwardIssueKey is required."""
        with pytest.raises(ValueError):
            asyncio.run(
                tool.execute({
                    "outwardIssueKey": "TEST-456",
                    "linkType": "Relates",
                })
            )

    def test_requires_outward_issue(self, tool: CreateIssueLinkTool) -> None:
        """Test that outwardIssueKey is required."""
        with pytest.raises(ValueError):
            asyncio.run(
                tool.execute({
                    "inwardIssueKey": "TEST-123",
                    "linkType": "Relates",
                })
            )

    def test_requires_link_type(self, tool: CreateIssueLinkTool) -> None:
        """Test that linkType is required."""
        with pytest.raises(ValueError):
            asyncio.run(
                tool.execute({
                    "inwardIssueKey": "TEST-123",
                    "outwardIssueKey": "TEST-456",
                })
            )

    def test_tool_definition(self, tool: CreateIssueLinkTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "create_issue_link"
        assert "inwardIssueKey" in definition.inputSchema["properties"]
        assert "outwardIssueKey" in definition.inputSchema["properties"]
        assert "linkType" in definition.inputSchema["properties"]
