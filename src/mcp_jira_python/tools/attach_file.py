from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class AttachFileTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="attach_file",
            description="Add the named filepath file as an attachment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to attach to",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the attachment file in issue",
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Filepath is file to attach",
                    },
                },
                "required": ["issueKey", "filename", "filepath"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        filename = arguments.get("filename")
        filepath_str = arguments.get("filepath")

        if not issue_key or not filename or not filepath_str:
            raise ValueError("issueKey, filename, and filepath are required")

        # Type narrowing: after the check above, these are guaranteed to be str
        filepath = Path(filepath_str)

        try:
            # Check if file exists
            if not filepath.exists():
                raise ValueError(f"File not found: {filepath}")

            # Check file size (10MB limit)
            if filepath.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("Attachment too large (max 10MB)")

            # Use add_attachment which is the correct method in the JIRA API
            self.jira.add_attachment(issue_key, str(filepath), filename=filename)

            return [
                TextContent(
                    type="text",
                    text=f'{{"message": "File attached successfully", "filename": "{filename}"}}',
                )
            ]

        except Exception as e:
            raise Exception(f"Failed to attach file: {e!s}") from e
