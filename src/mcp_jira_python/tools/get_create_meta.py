"""Tool for getting issue creation metadata including required fields."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..field_mapper import FieldMapper
from .base import BaseTool


class GetCreateMetaTool(BaseTool):
    """Tool to get metadata for creating issues, including required fields."""

    def __init__(self) -> None:
        super().__init__()
        self._field_mapper: FieldMapper | None = None

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_create_meta",
            description=(
                "Get metadata for creating issues in a project.\n\n"
                "Returns required and optional fields for each issue type. "
                "Use this before create_issue to know what fields are needed.\n\n"
                "Shows field names, types, and allowed values for select fields."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": "Project key (e.g., 'PROJ')",
                    },
                    "issueType": {
                        "type": "string",
                        "description": (
                            "Optional: specific issue type to get fields for "
                            "(e.g., 'Story', 'Bug'). If omitted, returns all types."
                        ),
                    },
                },
                "required": ["projectKey"],
            },
        )

    def _get_field_mapper(self) -> FieldMapper:
        """Get or create field mapper instance."""
        if self._field_mapper is None:
            if self.jira is None:
                raise RuntimeError("Jira client not initialized")
            self._field_mapper = FieldMapper(self.jira)
        return self._field_mapper

    def _format_field_info(self, field: dict[str, Any]) -> dict[str, Any]:
        """Format field information for output."""
        mapper = self._get_field_mapper()

        field_id = field.get("fieldId", field.get("key", ""))
        field_name = field.get("name", mapper.get_name(field_id) or field_id)

        info: dict[str, Any] = {
            "id": field_id,
            "name": field_name,
            "required": field.get("required", False),
        }

        # Get schema info
        schema = field.get("schema", {})
        if schema:
            info["type"] = schema.get("type", "unknown")
            if "items" in schema:
                info["itemType"] = schema["items"]

        # Get allowed values for select fields
        allowed_values = field.get("allowedValues", [])
        if allowed_values and len(allowed_values) <= 20:
            # Only include if reasonable number
            info["allowedValues"] = [
                v.get("name", v.get("value", str(v))) for v in allowed_values if isinstance(v, dict)
            ]

        return info

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        project_key = arguments.get("projectKey")
        issue_type_filter = arguments.get("issueType")

        if not project_key:
            raise ValueError("projectKey is required")

        try:
            # Get create metadata for the project
            # The expand parameter gets field information
            meta = self.jira.createmeta(
                projectKeys=project_key,
                expand="projects.issuetypes.fields",
            )

            if not meta.get("projects"):
                raise ValueError(f"Project {project_key} not found or no access")

            project = meta["projects"][0]
            issue_types = project.get("issuetypes", [])

            # Filter to specific issue type if requested
            if issue_type_filter:
                filter_lower = issue_type_filter.lower()
                issue_types = [
                    it for it in issue_types if it.get("name", "").lower() == filter_lower
                ]
                if not issue_types:
                    available = [it.get("name") for it in project.get("issuetypes", [])]
                    raise ValueError(
                        f"Issue type '{issue_type_filter}' not found. "
                        f"Available: {', '.join(available)}"
                    )

            # Build response
            result_types = []
            for issue_type in issue_types:
                fields = issue_type.get("fields", {})

                required_fields = []
                optional_fields = []

                for field_id, field_info in fields.items():
                    # Skip system fields that are auto-populated
                    if field_id in ("project", "issuetype"):
                        continue

                    formatted = self._format_field_info({**field_info, "fieldId": field_id})

                    if formatted["required"]:
                        required_fields.append(formatted)
                    else:
                        optional_fields.append(formatted)

                # Sort by name
                required_fields.sort(key=lambda x: x["name"])
                optional_fields.sort(key=lambda x: x["name"])

                result_types.append(
                    {
                        "name": issue_type.get("name"),
                        "description": issue_type.get("description", ""),
                        "requiredFields": required_fields,
                        "optionalFields": optional_fields[:15],  # Limit optional to top 15
                        "totalOptionalFields": len(optional_fields),
                    }
                )

            result = {
                "projectKey": project_key,
                "projectName": project.get("name", project_key),
                "issueTypes": result_types,
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get create metadata: {e!s}") from e

