"""Tool for getting available workflow transitions for a Jira issue."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class GetTransitionsTool(BaseTool):
    """Tool to get available workflow transitions for an issue."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_transitions",
            description=(
                "Get available workflow transitions for a Jira issue.\n\n"
                "Returns the list of states the issue can transition to from its "
                "current state. Use this to see what workflow actions are available.\n\n"
                "Example: An issue in 'In Progress' might be able to transition to "
                "'In Review', 'Blocked', or 'Done' depending on the workflow."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., 'PROJ-123')",
                    },
                },
                "required": ["issueKey"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        if not issue_key:
            raise ValueError("issueKey is required")

        try:
            # Get the issue to show current status
            issue = self.jira.issue(issue_key)
            current_status = str(issue.fields.status)

            # Get available transitions
            transitions = self.jira.transitions(issue_key)

            # Format transitions for output
            transition_list = []
            for t in transitions:
                transition_info: dict[str, Any] = {
                    "id": t["id"],
                    "name": t["name"],
                    "to": t.get("to", {}).get("name", "Unknown"),
                }

                # Include fields required for transition if any
                transition_fields = t.get("fields")
                if transition_fields:
                    required_fields = []
                    for field_id, field_info in transition_fields.items():
                        if field_info.get("required", False):
                            required_fields.append({
                                "id": field_id,
                                "name": field_info.get("name", field_id),
                            })
                    if required_fields:
                        transition_info["requiredFields"] = required_fields

                transition_list.append(transition_info)

            result = {
                "issueKey": issue_key,
                "currentStatus": current_status,
                "availableTransitions": transition_list,
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to get transitions: {e!s}") from e

