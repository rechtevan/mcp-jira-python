"""Tool for creating Jira issues with custom field support."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..field_mapper import FieldMapper
from .base import BaseTool


class CreateIssueTool(BaseTool):
    """Tool to create new Jira issues with support for custom fields."""

    def __init__(self) -> None:
        super().__init__()
        self._field_mapper: FieldMapper | None = None

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="create_jira_issue",
            description=(
                "Create a new Jira issue with standard and custom fields.\n\n"
                "Custom fields can be specified by friendly name (e.g., 'Story Points': 5) "
                "instead of internal IDs (customfield_10001).\n\n"
                "Use get_field_mapping tool to discover available custom fields.\n\n"
                "Supported Jira emoticons in description:\n"
                "- Smileys: :) :( :P :D ;)\n"
                "- Symbols: (y) (n) (i) (/) (x) (!)\n"
                "- Notation: (+) (-) (?) (on) (off) (*) (*r) (*g) (*b) (*y) (flag)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": "Project key (e.g., 'TEST')",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary/title",
                    },
                    "issueType": {
                        "type": "string",
                        "description": "Type of issue (e.g., 'Bug', 'Task', 'Story')",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Issue priority",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of the assignee",
                    },
                    "customFields": {
                        "type": "object",
                        "description": (
                            "Custom fields as key-value pairs. "
                            "Keys can be field names (e.g., 'Story Points') or IDs"
                        ),
                    },
                },
                "required": ["projectKey", "summary", "issueType"],
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
        project_key = arguments.get("projectKey")
        summary = arguments.get("summary")
        issue_type = arguments.get("issueType")

        if not project_key or not summary or not issue_type:
            raise ValueError("projectKey, summary, and issueType are required")

        # Build base issue dict
        issue_dict: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }

        # Add standard optional fields
        if "description" in arguments:
            issue_dict["description"] = arguments["description"]

        if "priority" in arguments:
            issue_dict["priority"] = {"name": arguments["priority"]}

        if "assignee" in arguments:
            issue_dict["assignee"] = {"emailAddress": arguments["assignee"]}

        # Add custom fields if provided
        custom_fields = arguments.get("customFields", {})
        if custom_fields:
            translated = self._translate_custom_fields(custom_fields)
            issue_dict.update(translated)

        issue = self.jira.create_issue(fields=issue_dict)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"key": issue.key, "id": issue.id, "self": issue.self},
                    indent=2,
                ),
            )
        ]
