import base64
import tempfile
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class AttachContentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="attach_content",
            description="Create and attach content directly to a Jira issue",
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
                    "content": {
                        "type": "string",
                        "description": "Content to include in the attachment",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Encoding of the content (none or base64)",
                        "enum": ["none", "base64"],
                        "default": "none",
                    },
                },
                "required": ["issueKey", "filename", "content"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        filename = arguments.get("filename")
        content = arguments.get("content")
        encoding = arguments.get("encoding", "none")

        if not all([issue_key, filename, content]):
            raise ValueError("issueKey, filename, and content are required")

        try:
            # Decode base64 content if specified
            if encoding == "base64":
                try:
                    content_bytes = base64.b64decode(content)
                except Exception as e:
                    raise ValueError(f"Failed to decode base64 content: {e!s}") from e
            else:
                # Convert string content to bytes with UTF-8 encoding
                content_bytes = content.encode("utf-8")

            # Check content size (10MB limit)
            if len(content_bytes) > 10 * 1024 * 1024:
                raise ValueError("Attachment too large (max 10MB)")

            # Create a temporary file to hold the content
            with tempfile.NamedTemporaryFile(delete=False, mode="wb") as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(content_bytes)

            try:
                # Use add_attachment with the temporary file
                self.jira.add_attachment(issue_key, str(temp_path), filename=filename)

                return [
                    TextContent(
                        type="text",
                        text=(
                            f'{{"message": "Content attached successfully", '
                            f'"filename": "{filename}"}}'
                        ),
                    )
                ]
            finally:
                # Clean up the temporary file
                if temp_path.exists():
                    temp_path.unlink()

        except UnicodeError:
            error_msg = (
                "Unicode encoding error: The content contains characters that "
                "couldn't be encoded. Try using base64 encoding."
            )
            return [
                TextContent(
                    type="text",
                    text=error_msg,
                )
            ]
        except Exception as e:
            raise Exception(f"Failed to attach content: {e!s}") from e
