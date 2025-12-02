from mcp.types import Tool

from .add_comment import AddCommentTool
from .add_comment_with_attachment import AddCommentWithAttachmentTool
from .attach_content import AttachContentTool
from .attach_file import AttachFileTool
from .base import BaseTool
from .create_issue import CreateIssueTool
from .create_issue_link import CreateIssueLinkTool
from .delete_issue import DeleteIssueTool
from .get_issue import GetIssueTool
from .get_issue_attachment import GetIssueAttachmentTool
from .get_user import GetUserTool
from .list_fields import ListFieldsTool
from .list_issue_types import ListIssueTypesTool
from .list_link_types import ListLinkTypesTool
from .search_issues import SearchIssuesTool
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
}


def get_all_tools() -> list[Tool]:
    return [tool.get_tool_definition() for tool in _TOOLS.values()]


def get_tool(name: str) -> BaseTool:
    if name not in _TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return _TOOLS[name]
