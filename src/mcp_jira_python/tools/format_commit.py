"""Tool for formatting git commit messages with Jira issue references."""

import json
import re
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class FormatCommitTool(BaseTool):
    """Tool to format commit messages with Jira issue references."""

    def get_tool_definition(self) -> Tool:
        return Tool(
            name="format_commit",
            description=(
                "Format a git commit message with proper Jira issue reference.\n\n"
                "Validates the issue exists and formats the commit message "
                "according to conventional commit style with Jira key.\n\n"
                "Formats:\n"
                "- Standard: 'PROJ-123: message'\n"
                "- Conventional: 'feat(PROJ-123): message'\n"
                "- Detailed: 'PROJ-123: message\\n\\nDescription...'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Jira issue key (e.g., 'PROJ-123')",
                    },
                    "message": {
                        "type": "string",
                        "description": "Commit message (without issue key)",
                    },
                    "type": {
                        "type": "string",
                        "description": (
                            "Conventional commit type: feat, fix, docs, style, "
                            "refactor, test, chore (optional)"
                        ),
                        "enum": [
                            "feat",
                            "fix",
                            "docs",
                            "style",
                            "refactor",
                            "test",
                            "chore",
                        ],
                    },
                    "includeDescription": {
                        "type": "boolean",
                        "description": "Include issue summary in commit body",
                        "default": False,
                    },
                    "validate": {
                        "type": "boolean",
                        "description": "Validate issue exists in Jira (default: true)",
                        "default": True,
                    },
                },
                "required": ["issueKey", "message"],
            },
        )

    def _validate_issue_key(self, issue_key: str) -> bool:
        """Check if string looks like a valid issue key."""
        pattern = r"^[A-Z][A-Z0-9]+-\d+$"
        return bool(re.match(pattern, issue_key.upper()))

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey", "").upper()
        message = arguments.get("message", "").strip()
        commit_type = arguments.get("type")
        include_description = arguments.get("includeDescription", False)
        validate = arguments.get("validate", True)

        if not issue_key:
            raise ValueError("issueKey is required")
        if not message:
            raise ValueError("message is required")

        # Validate issue key format
        if not self._validate_issue_key(issue_key):
            raise ValueError(f"Invalid issue key format: {issue_key}. Expected format: PROJ-123")

        issue_summary = None
        issue_type = None

        # Validate issue exists in Jira
        if validate:
            try:
                issue = self.jira.issue(issue_key, fields="summary,issuetype")
                issue_summary = issue.fields.summary
                issue_type = str(issue.fields.issuetype)
            except Exception as e:
                raise ValueError(f"Issue {issue_key} not found: {e!s}") from e

        # Build commit message
        if commit_type:
            # Conventional commit format
            subject = f"{commit_type}({issue_key}): {message}"
        else:
            # Standard format
            subject = f"{issue_key}: {message}"

        # Build full commit message
        commit_message = subject

        if include_description and issue_summary:
            commit_message += f"\n\nRelated to: {issue_summary}"
            if issue_type:
                commit_message += f"\nIssue type: {issue_type}"

        result: dict[str, Any] = {
            "issueKey": issue_key,
            "commitMessage": commit_message,
            "subject": subject,
        }

        if issue_summary:
            result["issueSummary"] = issue_summary

        # Add git command
        escaped_message = commit_message.replace('"', '\\"')
        result["gitCommand"] = f'git commit -m "{escaped_message}"'

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False),
            )
        ]
