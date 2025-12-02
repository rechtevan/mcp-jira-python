"""End-to-end tests for the MCP Jira server.

These tests verify the complete MCP server flow including:
- Tool listing
- Tool execution
- Error handling
"""

import pytest

from mcp_jira_python.tools import get_all_tools, get_tool


@pytest.mark.e2e
class TestMCPServerE2E:
    """End-to-end tests for MCP server functionality."""

    def test_list_all_tools(self) -> None:
        """Test that all tools are listed correctly."""
        tools = get_all_tools()

        assert len(tools) > 0
        tool_names = [tool.name for tool in tools]

        # Verify essential tools are present
        assert "get_issue" in tool_names
        assert "create_jira_issue" in tool_names
        assert "search_issues" in tool_names
        assert "update_issue" in tool_names
        assert "add_comment" in tool_names

    def test_get_tool_by_name(self) -> None:
        """Test retrieving a specific tool by name."""
        tool = get_tool("get_issue")

        assert tool is not None
        assert tool.get_tool_definition().name == "get_issue"

    def test_get_unknown_tool_raises(self) -> None:
        """Test that requesting an unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            get_tool("nonexistent_tool")

    def test_tool_definitions_have_required_fields(self) -> None:
        """Test that all tool definitions have required fields."""
        tools = get_all_tools()

        for tool in tools:
            assert tool.name, "Tool missing name"
            assert tool.description, f"Tool {tool.name} missing description"
            assert tool.inputSchema, f"Tool {tool.name} missing inputSchema"


@pytest.mark.e2e
@pytest.mark.integration
class TestMCPServerWithJira:
    """End-to-end tests that require a real Jira connection."""

    @pytest.mark.asyncio
    async def test_get_issue_flow(
        self, jira_client: "JIRA", test_project_key: str  # noqa: F821
    ) -> None:
        """Test the complete get_issue flow with real Jira."""
        from mcp_jira_python.tools.search_issues import SearchIssuesTool

        # First, search for an issue to get a valid key
        search_tool = SearchIssuesTool()
        search_tool.jira = jira_client

        result = await search_tool.execute({
            "projectKey": test_project_key,
            "jql": "ORDER BY updated DESC",
        })

        assert len(result) > 0
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_list_fields_flow(self, jira_client: "JIRA") -> None:  # noqa: F821
        """Test listing Jira fields."""
        from mcp_jira_python.tools.list_fields import ListFieldsTool

        tool = ListFieldsTool()
        tool.jira = jira_client

        result = await tool.execute({})

        assert len(result) > 0
        assert result[0].type == "text"
        # Should contain field information
        assert "id" in result[0].text
        assert "name" in result[0].text

    @pytest.mark.asyncio
    async def test_list_issue_types_flow(self, jira_client: "JIRA") -> None:  # noqa: F821
        """Test listing issue types."""
        from mcp_jira_python.tools.list_issue_types import ListIssueTypesTool

        tool = ListIssueTypesTool()
        tool.jira = jira_client

        result = await tool.execute({})

        assert len(result) > 0
        assert result[0].type == "text"

