"""Tool for retrieving Jira issue details including custom fields."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..field_mapper import FieldMapper
from .base import BaseTool


class GetIssueTool(BaseTool):
    """Tool to get complete issue details including custom fields."""

    def __init__(self) -> None:
        super().__init__()
        self._field_mapper: FieldMapper | None = None

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_issue",
            description=(
                "Get complete issue details including comments, attachments, and "
                "custom fields.\n\n"
                "By default, returns standard fields plus any custom fields with values.\n"
                "Custom field names are human-readable (e.g., 'Story Points').\n\n"
                "Options:\n"
                "- includeCustomFields: Include custom fields (default: true)\n"
                "- customFieldsOnly: Only return custom fields (default: false)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., PROJ-123)",
                    },
                    "includeCustomFields": {
                        "type": "boolean",
                        "description": "Include custom fields in response (default: true)",
                        "default": True,
                    },
                    "customFieldsOnly": {
                        "type": "boolean",
                        "description": "Only return custom fields (default: false)",
                        "default": False,
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

    def _format_field_value(self, value: Any) -> Any:
        """Format a field value for JSON output.

        Handles complex Jira field types like users, statuses, etc.
        """
        if value is None:
            return None

        # Handle lists (e.g., multi-select, sprints)
        if isinstance(value, list):
            return [self._format_field_value(item) for item in value]

        # Handle dicts - check for common patterns
        if isinstance(value, dict):
            for key in ("name", "value", "displayName"):
                if key in value:
                    return value[key]
            return value

        # Handle common Jira resource types (objects with specific attributes)
        for attr in ("displayName", "name", "value"):
            if hasattr(value, attr):
                return str(getattr(value, attr))

        # For primitive types, return as-is
        return value

    def _extract_custom_fields(self, issue: Any) -> dict[str, Any]:
        """Extract custom fields from an issue with friendly names."""
        mapper = self._get_field_mapper()
        custom_fields: dict[str, Any] = {}

        # Get raw fields from the issue
        raw_fields = issue.raw.get("fields", {})

        for field_id, value in raw_fields.items():
            # Only process custom fields (start with customfield_)
            if not field_id.startswith("customfield_"):
                continue

            # Skip null values
            if value is None:
                continue

            # Get friendly name
            field_name = mapper.get_name(field_id) or field_id

            # Format the value
            formatted_value = self._format_field_value(value)

            # Skip empty formatted values
            if formatted_value is None or formatted_value in ([], ""):
                continue

            custom_fields[field_name] = formatted_value

        return custom_fields

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        include_custom = arguments.get("includeCustomFields", True)
        custom_only = arguments.get("customFieldsOnly", False)

        if not issue_key:
            raise ValueError("issueKey is required")

        try:
            issue = self.jira.issue(issue_key, expand="comments,attachments")

            # Build response based on options
            if custom_only:
                # Only return custom fields
                issue_data: dict[str, Any] = {
                    "key": issue.key,
                    "customFields": self._extract_custom_fields(issue),
                }
            else:
                # Standard fields
                comments = [
                    {
                        "id": comment.id,
                        "author": str(comment.author),
                        "body": comment.body,
                        "created": str(comment.created),
                    }
                    for comment in issue.fields.comment.comments
                ]

                attachments = [
                    {
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "size": attachment.size,
                        "created": str(attachment.created),
                    }
                    for attachment in issue.fields.attachment
                ]

                issue_data = {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "description": issue.fields.description,
                    "status": str(issue.fields.status),
                    "priority": (
                        str(issue.fields.priority) if hasattr(issue.fields, "priority") else None
                    ),
                    "assignee": (
                        str(issue.fields.assignee) if hasattr(issue.fields, "assignee") else None
                    ),
                    "type": str(issue.fields.issuetype),
                    "comments": comments,
                    "attachments": attachments,
                }

                # Add custom fields if requested
                if include_custom:
                    issue_data["customFields"] = self._extract_custom_fields(issue)

            # Use json.dumps with ensure_ascii=False to properly handle Unicode
            return [
                TextContent(type="text", text=json.dumps(issue_data, ensure_ascii=False, indent=2))
            ]

        except UnicodeError as e:
            return [
                TextContent(
                    type="text",
                    text=f"Unicode encoding error while processing the issue: {e!s}",
                )
            ]
        except Exception as e:
            raise Exception(f"Failed to get issue: {e!s}") from e
