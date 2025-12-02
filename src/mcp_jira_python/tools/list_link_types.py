from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class ListLinkTypesTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="list_link_types",
            description="List all available issue link types",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        link_types = self.jira.issue_link_types()
        return [
            TextContent(
                type="text",
                text=str(
                    [
                        {"id": lt.id, "name": lt.name, "inward": lt.inward, "outward": lt.outward}
                        for lt in link_types
                    ]
                ),
            )
        ]
