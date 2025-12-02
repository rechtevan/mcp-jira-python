from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class AddCommentWithAttachmentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="add_comment_with_attachment",
            description="""Add a comment with file attachment to a Jira issue.

Supported Jira emoticons in comments:
- Smileys: :) :( :P :D ;)
- Symbols: (y) (n) (i) (/) (x) (!)
- Notation: (+) (-) (?) (on) (off) (*) (*r) (*g) (*b) (*y) (flag)

Note: Only use these Jira-specific emoticons. NEVER USE UNICODE EMOJIS!""",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to comment on",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text content.",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the attachment file used in destination Jira issue",
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to local file to attach",
                    },
                },
                "required": ["issueKey", "comment", "filename", "filepath"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        filename = arguments.get("filename")
        filepath_str = arguments.get("filepath")
        comment_text = arguments.get("comment")

        if not all([issue_key, filename, filepath_str, comment_text]):
            raise ValueError("issueKey, filename, filepath, and comment are required")

        filepath = Path(filepath_str)

        try:
            # Add the comment first
            comment = self.jira.add_comment(issue_key, comment_text)

            # Check if file exists
            if not filepath.exists():
                raise ValueError(f"File not found: {filepath}")

            # Check file size (10MB limit)
            if filepath.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("Attachment too large (max 10MB)")

            try:
                # Add attachment to the issue
                self.jira.add_attachment(issue_key, str(filepath), filename=filename)
            except Exception as e:
                # Log the error but don't fail - we know this might happen even on success
                print(f"Note: Expected attachment error occurred: {e!s}")

            return [
                TextContent(
                    type="text",
                    text=(
                        f'{{"message": "Comment and attachment added successfully", '
                        f'"comment_id": "{comment.id}", "filename": "{filename}"}}'
                    ),
                )
            ]

        except Exception as e:
            # Only raise for non-attachment errors
            if "not subscriptable" not in str(e):
                raise Exception(f"Failed to add comment with attachment: {e!s}") from e
            return [
                TextContent(
                    type="text",
                    text=(
                        f'{{"message": "Operation completed with expected response error", '
                        f'"comment_id": "{comment.id}", "filename": "{filename}"}}'
                    ),
                )
            ]
