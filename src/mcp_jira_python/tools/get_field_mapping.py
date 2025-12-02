"""Tool for discovering and exploring Jira field mappings."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class GetFieldMappingTool(BaseTool):
    """Tool to get field mapping information.

    This tool helps users discover available fields and their IDs,
    which is useful for working with custom fields.
    """

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_field_mapping",
            description="""Get Jira field mapping information.

Use this tool to:
- Discover available fields and their IDs
- Find custom field IDs for fields like "Story Points", "Sprint", etc.
- Search for fields by name pattern
- Get field type information

Returns field name, ID, type, and whether it's a custom field.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": (
                            "Optional search pattern to filter fields by name "
                            "(case-insensitive substring match)"
                        ),
                    },
                    "customOnly": {
                        "type": "boolean",
                        "description": "If true, only return custom fields",
                        "default": False,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of fields to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        search = arguments.get("search", "")
        custom_only = arguments.get("customOnly", False)
        limit = arguments.get("limit", 50)

        # Get all fields from Jira
        fields = self._jira_fields()

        # Filter by custom only if requested
        if custom_only:
            fields = [f for f in fields if f.get("custom", False)]

        # Filter by search pattern if provided
        if search:
            search_lower = search.lower()
            fields = [f for f in fields if search_lower in f.get("name", "").lower()]

        # Limit results
        fields = fields[:limit]

        # Format response
        result = [
            {
                "name": f.get("name"),
                "id": f.get("id"),
                "custom": f.get("custom", False),
                "type": f.get("schema", {}).get("type") if "schema" in f else None,
            }
            for f in fields
        ]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "fields": result,
                        "count": len(result),
                        "totalAvailable": len(self._jira_fields()),
                    },
                    indent=2,
                ),
            )
        ]

    def _jira_fields(self) -> list[dict[str, Any]]:
        """Get fields from Jira, caching the result."""
        # Use the jira client's fields() method
        return self.jira.fields()
