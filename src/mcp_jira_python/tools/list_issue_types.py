from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class ListIssueTypesTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_issue_types",
            description="List all available issue types",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_types = self.jira.issue_types()
        return [
            TextContent(
                type="text",
                text=str(
                    [
                        {
                            "id": it.id,
                            "name": it.name,
                            "description": it.description,
                            "subtask": it.subtask,
                        }
                        for it in issue_types
                    ]
                ),
            )
        ]
