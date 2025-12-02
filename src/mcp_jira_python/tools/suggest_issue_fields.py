"""Tool for suggesting fields and values when creating issues."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class SuggestIssueFieldsTool(BaseTool):
    """Tool to suggest fields and guide issue creation."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="suggest_issue_fields",
            description=(
                "Get suggestions for creating a well-formed Jira issue.\n\n"
                "Analyzes the project and issue type to suggest:\n"
                "- Required fields that must be filled\n"
                "- Recommended fields (epic link, story points, etc.)\n"
                "- Available epics to link to\n\n"
                "Use before create_issue to ensure complete issue creation."
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
                        "description": "Issue type (e.g., 'Story', 'Bug', 'Task')",
                    },
                },
                "required": ["projectKey", "issueType"],
            },
        )

    def _get_recommendations(self, issue_type_lower: str) -> list[dict[str, Any]]:
        """Get field recommendations based on issue type."""
        recommendations: list[dict[str, Any]] = []

        if issue_type_lower in ("story", "user story"):
            recommendations = [
                {
                    "field": "Story Points",
                    "reason": "Helps with sprint planning",
                    "suggestedValues": [1, 2, 3, 5, 8, 13],
                },
                {
                    "field": "Epic Link",
                    "reason": "Stories should belong to an epic",
                },
            ]
        elif issue_type_lower == "bug":
            recommendations = [
                {"field": "Priority", "reason": "Helps triage bugs"},
                {
                    "field": "Steps to Reproduce",
                    "reason": "Add to description for faster debugging",
                },
            ]
        elif issue_type_lower == "task":
            recommendations = [
                {
                    "field": "Story Points",
                    "reason": "Tasks benefit from estimation",
                    "suggestedValues": [1, 2, 3, 5],
                },
            ]
        elif issue_type_lower == "epic":
            recommendations = [
                {"field": "Epic Name", "reason": "Short name for linked issues"},
            ]

        return recommendations

    def _extract_fields(
        self, fields: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Extract required and optional fields from metadata."""
        required_fields = []
        optional_fields = []

        for field_id, field_info in fields.items():
            if field_id in ("project", "issuetype"):
                continue

            field_data: dict[str, Any] = {
                "id": field_id,
                "name": field_info.get("name", field_id),
            }

            allowed = field_info.get("allowedValues", [])
            if allowed and len(allowed) <= 10:
                field_data["allowedValues"] = [
                    v.get("name", v.get("value", str(v)))
                    for v in allowed
                    if isinstance(v, dict)
                ]

            if field_info.get("required"):
                required_fields.append(field_data)
            elif field_id in ("priority", "labels", "components"):
                optional_fields.append(field_data)

        return required_fields, optional_fields

    def _get_available_epics(self, project_key: str) -> list[dict[str, str]]:
        """Get open epics in the project."""
        try:
            epics = self.jira.search_issues(
                f"project = {project_key} AND issuetype = Epic "
                "AND status != Done ORDER BY created DESC",
                maxResults=5,
                fields="summary",
            )
            return [{"key": e.key, "summary": e.fields.summary} for e in epics]
        except Exception:
            return []

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        project_key = arguments.get("projectKey")
        issue_type = arguments.get("issueType")

        if not project_key:
            raise ValueError("projectKey is required")
        if not issue_type:
            raise ValueError("issueType is required")

        try:
            # Get create metadata
            meta = self.jira.createmeta(
                projectKeys=project_key,
                expand="projects.issuetypes.fields",
            )

            if not meta.get("projects"):
                raise ValueError(f"Project {project_key} not found")

            project = meta["projects"][0]
            issue_types = project.get("issuetypes", [])

            # Find matching issue type
            issue_type_lower = issue_type.lower()
            matching_type = next(
                (it for it in issue_types if it.get("name", "").lower() == issue_type_lower),
                None,
            )

            if not matching_type:
                available = [it.get("name") for it in issue_types]
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Issue type '{issue_type}' not found",
                            "availableTypes": available,
                        }, indent=2),
                    )
                ]

            # Extract fields
            fields = matching_type.get("fields", {})
            required_fields, _ = self._extract_fields(fields)

            # Build result
            result: dict[str, Any] = {
                "projectKey": project_key,
                "issueType": issue_type,
                "requiredFields": required_fields,
                "recommendations": self._get_recommendations(issue_type_lower),
            }

            # Add epics for non-epic types
            if issue_type_lower != "epic":
                epics = self._get_available_epics(project_key)
                if epics:
                    result["availableEpics"] = epics

            result["tips"] = [
                "Use get_create_meta for full field details",
                "Custom fields can use friendly names",
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get suggestions: {e!s}") from e
