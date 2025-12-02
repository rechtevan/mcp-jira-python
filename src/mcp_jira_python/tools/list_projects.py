"""Tool for listing Jira projects."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class ListProjectsTool(BaseTool):
    """Tool to list available Jira projects."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_projects",
            description=(
                "List all Jira projects you have access to.\n\n"
                "Returns project key, name, and lead. Use this to discover "
                "available projects before creating issues or searching."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Optional: filter projects by name or key (case-insensitive)"
                        ),
                    },
                    "maxResults": {
                        "type": "integer",
                        "description": "Maximum number of projects to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        query = arguments.get("query", "")
        max_results = arguments.get("maxResults", 50)

        try:
            # Get all projects
            projects = self.jira.projects()

            # Filter if query provided
            if query:
                query_lower = query.lower()
                projects = [
                    p
                    for p in projects
                    if query_lower in p.key.lower() or query_lower in p.name.lower()
                ]

            # Limit results
            projects = projects[:max_results]

            # Build response
            project_list = []
            for project in projects:
                project_info: dict[str, Any] = {
                    "key": project.key,
                    "name": project.name,
                }

                # Add lead if available
                if hasattr(project, "lead") and project.lead:
                    project_info["lead"] = str(project.lead)

                # Add project type if available
                if hasattr(project, "projectTypeKey"):
                    project_info["type"] = project.projectTypeKey

                project_list.append(project_info)

            result = {
                "count": len(project_list),
                "projects": project_list,
            }

            if query:
                result["filter"] = query

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to list projects: {e!s}") from e


