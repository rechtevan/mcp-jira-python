"""Tool for updating Jira issues with custom field support."""

from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

from ..field_mapper import FieldMapper
from .base import BaseTool

if TYPE_CHECKING:
    from collections.abc import Callable


class UpdateIssueTool(BaseTool):
    """Tool to update existing Jira issues with support for custom fields."""

    def __init__(self) -> None:
        super().__init__()
        self._field_mapper: FieldMapper | None = None

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="update_issue",
            description=(
                "Update an existing Jira issue with standard and custom fields.\n\n"
                "Custom fields can be specified by friendly name (e.g., 'Story Points': 5) "
                "instead of internal IDs.\n\n"
                "Use get_field_mapping tool to discover available custom fields."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to update (e.g., 'PROJ-123')",
                    },
                    "summary": {
                        "type": "string",
                        "description": "New summary/title",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of new assignee",
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority",
                    },
                    "customFields": {
                        "type": "object",
                        "description": (
                            "Custom fields to update as key-value pairs. "
                            "Keys can be field names (e.g., 'Story Points') or IDs"
                        ),
                    },
                },
                "required": ["issueKey"],
            },
        )

    def _get_field_mapper(self) -> FieldMapper:
        """Get or create field mapper instance."""
        if self._field_mapper is None:
            if self.jira is None:
                raise RuntimeError("Jira client not initialized")
            self._field_mapper = FieldMapper(self.jira)
        return self._field_mapper

    def _translate_custom_fields(self, custom_fields: dict[str, Any]) -> dict[str, Any]:
        """Translate custom field names to IDs."""
        mapper = self._get_field_mapper()
        return mapper.translate_fields(custom_fields)

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        if not issue_key:
            raise ValueError("issueKey is required")

        update_fields: dict[str, Any] = {}

        # Standard field mappings
        field_mappings: dict[str, Callable[[Any], Any]] = {
            "summary": lambda x: x,
            "description": lambda x: x,
            "assignee": lambda x: {"emailAddress": x},
            "priority": lambda x: {"name": x},
        }

        for field, transform in field_mappings.items():
            if field in arguments:
                update_fields[field] = transform(arguments[field])

        # Add custom fields if provided
        custom_fields = arguments.get("customFields", {})
        if custom_fields:
            translated = self._translate_custom_fields(custom_fields)
            update_fields.update(translated)

        issue = self.jira.issue(issue_key)
        issue.update(fields=update_fields)

        return [
            TextContent(
                type="text",
                text=f'{{"message": "Issue {issue_key} updated successfully"}}',
            )
        ]
