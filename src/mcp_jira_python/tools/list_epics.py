"""Tool for listing epics in a Jira project."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class ListEpicsTool(BaseTool):
    """Tool to list epics in a project."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_epics",
            description=(
                "List epics in a Jira project.\n\n"
                "Returns epics with their key, summary, status, and child issue count. "
                "Useful for finding which epic a new story should belong to.\n\n"
                "Filter by status to show only open epics, or include all."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": "Project key (e.g., 'PROJ')",
                    },
                    "status": {
                        "type": "string",
                        "description": (
                            "Filter by status: 'open', 'done', or 'all' (default: 'open')"
                        ),
                        "enum": ["open", "done", "all"],
                        "default": "open",
                    },
                    "maxResults": {
                        "type": "integer",
                        "description": "Maximum number of epics to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": ["projectKey"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        project_key = arguments.get("projectKey")
        status_filter = arguments.get("status", "open")
        max_results = arguments.get("maxResults", 50)

        if not project_key:
            raise ValueError("projectKey is required")

        try:
            # Build JQL for epics
            jql_parts = [
                f"project = {project_key}",
                "issuetype = Epic",
            ]

            # Add status filter
            if status_filter == "open":
                jql_parts.append("status != Done")
            elif status_filter == "done":
                jql_parts.append("status = Done")
            # "all" doesn't add a status filter

            jql_parts.append("ORDER BY created DESC")
            jql = " AND ".join(jql_parts[:-1]) + " " + jql_parts[-1]

            # Search for epics
            epics = self.jira.search_issues(
                jql,
                maxResults=max_results,
                fields="summary,status,priority,assignee",
            )

            # Build response
            epic_list = []
            for epic in epics:
                epic_info: dict[str, Any] = {
                    "key": epic.key,
                    "summary": epic.fields.summary,
                    "status": str(epic.fields.status),
                }

                if hasattr(epic.fields, "priority") and epic.fields.priority:
                    epic_info["priority"] = str(epic.fields.priority)

                if hasattr(epic.fields, "assignee") and epic.fields.assignee:
                    epic_info["assignee"] = str(epic.fields.assignee)

                epic_list.append(epic_info)

            result = {
                "projectKey": project_key,
                "filter": status_filter,
                "count": len(epic_list),
                "epics": epic_list,
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to list epics: {e!s}") from e


