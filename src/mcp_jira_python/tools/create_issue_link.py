from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class CreateIssueLinkTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="create_issue_link",
            description="Create a link between two issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "inwardIssueKey": {
                        "type": "string",
                        "description": "Key of the inward issue (e.g., blocked issue)",
                    },
                    "outwardIssueKey": {
                        "type": "string",
                        "description": "Key of the outward issue (e.g., blocking issue)",
                    },
                    "linkType": {
                        "type": "string",
                        "description": "Type of link (e.g., 'blocks')",
                    },
                },
                "required": ["inwardIssueKey", "outwardIssueKey", "linkType"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        inward_issue = arguments.get("inwardIssueKey")
        outward_issue = arguments.get("outwardIssueKey")
        link_type = arguments.get("linkType")

        if not all([inward_issue, outward_issue, link_type]):
            raise ValueError("inwardIssueKey, outwardIssueKey, and linkType are required")

        self.jira.create_issue_link(
            type=link_type, inwardIssue=inward_issue, outwardIssue=outward_issue
        )

        return [
            TextContent(
                type="text",
                text=(
                    f'{{"message": "Issue link created successfully", '
                    f'"inwardIssue": "{inward_issue}", '
                    f'"outwardIssue": "{outward_issue}", '
                    f'"linkType": "{link_type}"}}'
                ),
            )
        ]
