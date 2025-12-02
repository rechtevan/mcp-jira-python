"""Tool for transitioning a Jira issue to a new workflow state."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..field_mapper import FieldMapper
from .base import BaseTool


class TransitionIssueTool(BaseTool):
    """Tool to transition an issue to a new workflow state."""

    def __init__(self) -> None:
        super().__init__()
        self._field_mapper: FieldMapper | None = None

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="transition_issue",
            description=(
                "Transition a Jira issue to a new workflow state.\n\n"
                "Use get_transitions first to see available transitions. You can specify "
                "the transition by name (e.g., 'Done', 'In Progress') or by ID.\n\n"
                "Some transitions require additional fields - use the fields parameter "
                "to provide them. Field names can be friendly names or IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., 'PROJ-123')",
                    },
                    "transition": {
                        "type": "string",
                        "description": ("Transition name (e.g., 'Done', 'Start Progress') or ID"),
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment to add with the transition",
                    },
                    "fields": {
                        "type": "object",
                        "description": (
                            "Fields required for the transition (e.g., resolution). "
                            "Can use friendly field names."
                        ),
                    },
                },
                "required": ["issueKey", "transition"],
            },
        )

    def _get_field_mapper(self) -> FieldMapper:
        """Get or create field mapper instance."""
        if self._field_mapper is None:
            if self.jira is None:
                raise RuntimeError("Jira client not initialized")
            self._field_mapper = FieldMapper(self.jira)
        return self._field_mapper

    def _find_transition(self, issue_key: str, transition_name_or_id: str) -> dict[str, Any] | None:
        """Find a transition by name or ID."""
        transitions: list[dict[str, Any]] = self.jira.transitions(issue_key)

        # Try exact ID match first
        for t in transitions:
            if t["id"] == transition_name_or_id:
                return t

        # Try case-insensitive name match
        name_lower = transition_name_or_id.lower()
        for t in transitions:
            if t["name"].lower() == name_lower:
                return t

        # Try partial name match
        for t in transitions:
            if name_lower in t["name"].lower():
                return t

        return None

    def _translate_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Translate field names to IDs."""
        mapper = self._get_field_mapper()
        return mapper.translate_fields(fields)

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        transition_input = arguments.get("transition")
        comment = arguments.get("comment")
        fields = arguments.get("fields", {})

        if not issue_key:
            raise ValueError("issueKey is required")
        if not transition_input:
            raise ValueError("transition is required")

        try:
            # Find the transition
            transition = self._find_transition(issue_key, transition_input)

            if not transition:
                # Get available transitions for helpful error
                available = self.jira.transitions(issue_key)
                available_names = [t["name"] for t in available]
                raise ValueError(
                    f"Transition '{transition_input}' not available. "
                    f"Available transitions: {', '.join(available_names)}"
                )

            # Get current status for response
            issue = self.jira.issue(issue_key)
            from_status = str(issue.fields.status)
            to_status = transition.get("to", {}).get("name", "Unknown")

            # Prepare transition kwargs
            transition_kwargs: dict[str, Any] = {}

            # Add comment if provided
            if comment:
                transition_kwargs["comment"] = comment

            # Translate and add fields if provided
            if fields:
                translated_fields = self._translate_fields(fields)
                transition_kwargs["fields"] = translated_fields

            # Perform the transition
            self.jira.transition_issue(issue_key, transition["id"], **transition_kwargs)

            result = {
                "message": f"Issue {issue_key} transitioned successfully",
                "issueKey": issue_key,
                "from": from_status,
                "to": to_status,
                "transition": transition["name"],
            }

            if comment:
                result["comment"] = "Added"

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to transition issue: {e!s}") from e
