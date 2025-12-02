"""Tool for getting issues that belong to an epic."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class GetEpicIssuesTool(BaseTool):
    """Tool to get issues belonging to an epic."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_epic_issues",
            description=(
                "Get all issues that belong to an epic.\n\n"
                "Returns stories, tasks, and bugs linked to the specified epic. "
                "Useful for seeing epic progress and what work remains."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "epicKey": {
                        "type": "string",
                        "description": "Epic issue key (e.g., 'PROJ-100')",
                    },
                    "status": {
                        "type": "string",
                        "description": (
                            "Filter by status: 'open', 'done', or 'all' (default: 'all')"
                        ),
                        "enum": ["open", "done", "all"],
                        "default": "all",
                    },
                    "maxResults": {
                        "type": "integer",
                        "description": "Maximum number of issues to return (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["epicKey"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        epic_key = arguments.get("epicKey")
        status_filter = arguments.get("status", "all")
        max_results = arguments.get("maxResults", 100)

        if not epic_key:
            raise ValueError("epicKey is required")

        try:
            # Get the epic first to verify it exists and get info
            epic = self.jira.issue(epic_key)
            epic_summary = epic.fields.summary

            # Build JQL for issues in the epic
            # "Epic Link" is the standard field, but some instances use parent
            # Try both approaches
            jql_parts = [f'"Epic Link" = {epic_key}']

            # Add status filter
            if status_filter == "open":
                jql_parts.append("status != Done")
            elif status_filter == "done":
                jql_parts.append("status = Done")

            jql_parts.append("ORDER BY status ASC, priority DESC")
            jql = " AND ".join(jql_parts[:-1]) + " " + jql_parts[-1]

            # Search for issues in the epic
            issues = self.jira.search_issues(
                jql,
                maxResults=max_results,
                fields="summary,status,issuetype,priority,assignee,customfield_10001",
            )

            # Build response with progress stats
            issue_list = []
            done_count = 0
            total_points = 0
            done_points = 0

            for issue in issues:
                issue_info: dict[str, Any] = {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "type": str(issue.fields.issuetype),
                    "status": str(issue.fields.status),
                }

                if hasattr(issue.fields, "priority") and issue.fields.priority:
                    issue_info["priority"] = str(issue.fields.priority)

                if hasattr(issue.fields, "assignee") and issue.fields.assignee:
                    issue_info["assignee"] = str(issue.fields.assignee)

                # Try to get story points (common custom field)
                story_points = getattr(issue.fields, "customfield_10001", None)
                if story_points:
                    issue_info["storyPoints"] = story_points
                    total_points += story_points

                # Track done status
                status_str = str(issue.fields.status).lower()
                if status_str in {"done", "closed"}:
                    done_count += 1
                    if story_points:
                        done_points += story_points

                issue_list.append(issue_info)

            # Calculate progress
            total_count = len(issue_list)
            progress_pct = (done_count / total_count * 100) if total_count > 0 else 0
            points_pct = (done_points / total_points * 100) if total_points > 0 else 0

            result = {
                "epicKey": epic_key,
                "epicSummary": epic_summary,
                "filter": status_filter,
                "progress": {
                    "totalIssues": total_count,
                    "doneIssues": done_count,
                    "percentComplete": round(progress_pct, 1),
                    "totalPoints": total_points,
                    "donePoints": done_points,
                    "pointsPercentComplete": round(points_pct, 1),
                },
                "issues": issue_list,
            }

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to get epic issues: {e!s}") from e

