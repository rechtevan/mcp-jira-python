from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from .base import BaseTool


class GetIssueAttachmentTool(BaseTool):
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="get_issue_attachment",
            description=(
                "Download an attachment from a Jira issue to a local file. "
                "If neither attachmentId nor filename is provided, all attachments "
                "will be downloaded. Original filenames preserved."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue containing the attachment",
                    },
                    "attachmentId": {
                        "type": "string",
                        "description": (
                            "ID of the attachment to download (optional if filename is provided)"
                        ),
                    },
                    "filename": {
                        "type": "string",
                        "description": (
                            "Name of the attachment file to download "
                            "(optional if attachmentId is provided)"
                        ),
                    },
                    "outputPath": {
                        "type": "string",
                        "description": (
                            "Local path where to save the downloaded file "
                            "(optional, defaults to current directory with original filename)"
                        ),
                    },
                },
                "required": ["issueKey"],
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        issue_key = arguments.get("issueKey")
        attachment_id = arguments.get("attachmentId")
        filename = arguments.get("filename")
        output_path_str = arguments.get("outputPath", ".")

        if not issue_key:
            raise ValueError("issueKey is required")

        # If neither attachment_id nor filename is provided, download all attachments
        download_all = not attachment_id and not filename

        # If no output path specified, use current directory
        output_path = Path(output_path_str or ".")

        try:
            # Create output directory if it doesn't exist
            output_path.resolve().mkdir(parents=True, exist_ok=True)

            # If attachment_id is provided, download directly
            if attachment_id:
                attachment = self.jira.attachment(attachment_id)
                file_path = output_path / attachment.filename

                # Download the content
                attachment_data = attachment.get()

                # Write to file
                file_path.write_bytes(attachment_data)

                return [
                    TextContent(
                        type="text",
                        text=str(
                            {
                                "message": "Attachment downloaded successfully",
                                "filename": attachment.filename,
                                "path": str(file_path),
                                "size": attachment.size,
                            }
                        ),
                    )
                ]

            # Get issue with attachments
            issue = self.jira.issue(issue_key, expand="attachments")

            if not hasattr(issue.fields, "attachment") or not issue.fields.attachment:
                raise ValueError(f"No attachments found in issue {issue_key}")

            # If download_all is True, download all attachments
            if download_all:
                downloaded_files = []

                for attachment in issue.fields.attachment:
                    file_path = output_path / attachment.filename

                    # Download the content
                    attachment_data = attachment.get()

                    # Write to file
                    file_path.write_bytes(attachment_data)

                    downloaded_files.append(
                        {
                            "filename": attachment.filename,
                            "path": str(file_path),
                            "size": attachment.size,
                            "id": attachment.id,
                        }
                    )

                return [
                    TextContent(
                        type="text",
                        text=str(
                            {
                                "message": f"Downloaded {len(downloaded_files)} attachments",
                                "files": downloaded_files,
                                "outputPath": str(output_path),
                            }
                        ),
                    )
                ]

            # If filename is provided, find the specific attachment
            for attachment in issue.fields.attachment:
                if attachment.filename == filename:
                    file_path = output_path / attachment.filename

                    # Download the content
                    attachment_data = attachment.get()

                    # Write to file
                    file_path.write_bytes(attachment_data)

                    return [
                        TextContent(
                            type="text",
                            text=str(
                                {
                                    "message": "Attachment downloaded successfully",
                                    "filename": attachment.filename,
                                    "path": str(file_path),
                                    "size": attachment.size,
                                    "id": attachment.id,
                                }
                            ),
                        )
                    ]

            raise ValueError(f"Attachment '{filename}' not found in issue {issue_key}")

        except Exception as e:
            raise Exception(f"Failed to download attachment: {e!s}") from e
