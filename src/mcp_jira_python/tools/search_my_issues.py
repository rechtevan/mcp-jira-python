"""Tool for searching issues assigned to the current user."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class SearchMyIssuesTool(BaseTool):
    """Tool to search issues assigned to or reported by the current user."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="search_my_issues",
            description=(
                "Search for Jira issues assigned to you or that you're watching.\n\n"
                "Quick way to find issues you're working on for commit messages. "
                "Returns issue key, summary, and status - perfect for referencing "
                "in git commits.\n\n"
                "Example: Find your in-progress issues to include in commit message."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": "Optional: filter to specific project",
                    },
                    "status": {
                        "type": "string",
                        "description": (
                            "Filter by status: 'in_progress', 'open', 'all' "
                            "(default: 'in_progress')"
                        ),
                        "enum": ["in_progress", "open", "all"],
                        "default": "in_progress",
                    },
                    "role": {
                        "type": "string",
                        "description": (
                            "Your role: 'assignee', 'reporter', 'watcher', 'any' "
                            "(default: 'assignee')"
                        ),
                        "enum": ["assignee", "reporter", "watcher", "any"],
                        "default": "assignee",
                    },
                    "maxResults": {
                        "type": "integer",
                        "description": "Maximum results (default: 10)",
                        "default": 10,
                    },
                },
                "required": [],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        project_key = arguments.get("projectKey")
        status_filter = arguments.get("status", "in_progress")
        role = arguments.get("role", "assignee")
        max_results = arguments.get("maxResults", 10)

        try:
            # Build JQL
            jql_parts = []

            # Role filter
            if role == "assignee":
                jql_parts.append("assignee = currentUser()")
            elif role == "reporter":
                jql_parts.append("reporter = currentUser()")
            elif role == "watcher":
                jql_parts.append("watcher = currentUser()")
            else:  # any
                jql_parts.append(
                    "(assignee = currentUser() OR reporter = currentUser() "
                    "OR watcher = currentUser())"
                )

            # Project filter
            if project_key:
                jql_parts.append(f"project = {project_key}")

            # Status filter
            if status_filter == "in_progress":
                jql_parts.append('status = "In Progress"')
            elif status_filter == "open":
                jql_parts.append("status != Done AND status != Closed")

            jql_parts.append("ORDER BY updated DESC")
            jql = " AND ".join(jql_parts[:-1]) + " " + jql_parts[-1]

            # Search
            issues = self.jira.search_issues(
                jql,
                maxResults=max_results,
                fields="summary,status,issuetype,priority,project",
            )

            # Build response
            issue_list = []
            for issue in issues:
                issue_info: dict[str, Any] = {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": str(issue.fields.status),
                    "type": str(issue.fields.issuetype),
                    "project": issue.fields.project.key,
                }

                # Add commit format hint
                issue_info["commitFormat"] = f"{issue.key}: "

                issue_list.append(issue_info)

            result: dict[str, Any] = {
                "count": len(issue_list),
                "issues": issue_list,
            }

            if project_key:
                result["projectFilter"] = project_key
            result["statusFilter"] = status_filter
            result["roleFilter"] = role

            # Add helpful hint
            if issue_list:
                result["hint"] = (
                    f'Use issue key in commit: git commit -m "{issue_list[0]["key"]}: your message"'
                )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to search issues: {e!s}") from e

