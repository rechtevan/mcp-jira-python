"""MCP tools for Jira integration.

This module provides all available tools for the Jira MCP server.
Each tool is a class that implements the BaseTool interface.
"""

from mcp.types import Tool

from .add_comment import AddCommentTool
from .add_comment_with_attachment import AddCommentWithAttachmentTool
from .attach_content import AttachContentTool
from .attach_file import AttachFileTool
from .audit_issue import AuditIssueTool
from .base import BaseTool
from .create_issue import CreateIssueTool
from .create_issue_link import CreateIssueLinkTool
from .delete_issue import DeleteIssueTool
from .format_commit import FormatCommitTool
from .get_create_meta import GetCreateMetaTool
from .get_epic_issues import GetEpicIssuesTool
from .get_field_mapping import GetFieldMappingTool
from .get_issue import GetIssueTool
from .get_issue_attachment import GetIssueAttachmentTool
from .get_transitions import GetTransitionsTool
from .get_user import GetUserTool
from .list_epics import ListEpicsTool
from .list_fields import ListFieldsTool
from .list_issue_types import ListIssueTypesTool
from .list_link_types import ListLinkTypesTool
from .list_projects import ListProjectsTool
from .search_issues import SearchIssuesTool
from .search_my_issues import SearchMyIssuesTool
from .suggest_issue_fields import SuggestIssueFieldsTool
from .transition_issue import TransitionIssueTool
from .update_issue import UpdateIssueTool

_TOOLS: dict[str, BaseTool] = {
    "delete_issue": DeleteIssueTool(),
    "create_jira_issue": CreateIssueTool(),
    "get_issue": GetIssueTool(),
    "get_issue_attachment": GetIssueAttachmentTool(),
    "create_issue_link": CreateIssueLinkTool(),
    "update_issue": UpdateIssueTool(),
    "get_user": GetUserTool(),
    "list_fields": ListFieldsTool(),
    "list_issue_types": ListIssueTypesTool(),
    "list_link_types": ListLinkTypesTool(),
    "search_issues": SearchIssuesTool(),
    "add_comment": AddCommentTool(),
    "add_comment_with_attachment": AddCommentWithAttachmentTool(),
    "attach_file": AttachFileTool(),
    "attach_content": AttachContentTool(),
    "get_field_mapping": GetFieldMappingTool(),
    "get_transitions": GetTransitionsTool(),
    "transition_issue": TransitionIssueTool(),
    "list_epics": ListEpicsTool(),
    "get_epic_issues": GetEpicIssuesTool(),
    "get_create_meta": GetCreateMetaTool(),
    "list_projects": ListProjectsTool(),
    "search_my_issues": SearchMyIssuesTool(),
    "format_commit": FormatCommitTool(),
    "suggest_issue_fields": SuggestIssueFieldsTool(),
    "audit_issue": AuditIssueTool(),
}


def get_all_tools() -> list[Tool]:
    """Get tool definitions for all registered tools.

    Returns:
        List of Tool definitions for MCP server registration.
    """
    return [tool.get_tool_definition() for tool in _TOOLS.values()]


def get_tool(name: str) -> BaseTool:
    """Get a tool instance by name.

    Args:
        name: The tool name (e.g., 'create_jira_issue', 'get_issue').

    Returns:
        The tool instance.

    Raises:
        ValueError: If the tool name is not found.
    """
    if name not in _TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return _TOOLS[name]
