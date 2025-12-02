"""Unit tests for AddCommentWithAttachmentTool."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.add_comment_with_attachment import AddCommentWithAttachmentTool


@pytest.fixture
def mock_attachment() -> Mock:
    """Mock attachment."""
    attachment = Mock()
    attachment.id = "67890"
    attachment.filename = "test.txt"
    return attachment


@pytest.fixture
def mock_comment() -> Mock:
    """Mock comment."""
    comment = Mock()
    comment.id = "12345"
    comment.body = "Test comment with attachment"
    return comment


@pytest.fixture
def mock_jira(mock_attachment: Mock, mock_comment: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.add_attachment.return_value = [mock_attachment]
    jira.add_comment.return_value = mock_comment
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> AddCommentWithAttachmentTool:
    """Create tool with mock Jira."""
    tool = AddCommentWithAttachmentTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestAddCommentWithAttachmentTool:
    """Tests for AddCommentWithAttachmentTool."""

    def test_execute_success(self, tool: AddCommentWithAttachmentTool, mock_jira: Mock) -> None:
        """Test adding a comment with attachment successfully."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write("Test file content")
            tmp_path = Path(tmp.name)

        try:
            result = asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "comment": "Test comment with attachment",
                        "filename": "test.txt",
                        "filepath": str(tmp_path),
                    }
                )
            )

            assert result[0].type == "text"
            assert "12345" in result[0].text  # Comment ID
            assert "test.txt" in result[0].text

            mock_jira.add_comment.assert_called_with("TEST-123", "Test comment with attachment")
            mock_jira.add_attachment.assert_called_once()
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_tool_definition(self, tool: AddCommentWithAttachmentTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "add_comment_with_attachment"
        assert "issueKey" in definition.inputSchema["properties"]
        assert "comment" in definition.inputSchema["properties"]
        assert "filename" in definition.inputSchema["properties"]
        assert "filepath" in definition.inputSchema["properties"]

    def test_execute_missing_required_fields(self, tool: AddCommentWithAttachmentTool) -> None:
        """Test error when required fields are missing."""
        with pytest.raises(
            ValueError, match="issueKey, filename, filepath, and comment are required"
        ):
            asyncio.run(tool.execute({"issueKey": "TEST-123"}))

    def test_execute_file_not_found(
        self, tool: AddCommentWithAttachmentTool, mock_jira: Mock
    ) -> None:
        """Test error when file does not exist."""
        with pytest.raises(Exception, match="File not found"):
            asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "comment": "Test comment",
                        "filename": "test.txt",
                        "filepath": "/nonexistent/path/file.txt",
                    }
                )
            )

    def test_execute_file_too_large(
        self, tool: AddCommentWithAttachmentTool, mock_jira: Mock
    ) -> None:
        """Test error when file exceeds size limit."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as tmp:
            # Write more than 10MB
            tmp.write(b"x" * (11 * 1024 * 1024))
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(Exception, match="Attachment too large"):
                asyncio.run(
                    tool.execute(
                        {
                            "issueKey": "TEST-123",
                            "comment": "Test comment",
                            "filename": "large.txt",
                            "filepath": str(tmp_path),
                        }
                    )
                )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_execute_attachment_error_handled(
        self, tool: AddCommentWithAttachmentTool, mock_jira: Mock
    ) -> None:
        """Test that attachment errors are handled gracefully."""
        mock_jira.add_attachment.side_effect = Exception("Upload failed")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            tmp.write("Test content")
            tmp_path = Path(tmp.name)

        try:
            result = asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "comment": "Test comment",
                        "filename": "test.txt",
                        "filepath": str(tmp_path),
                    }
                )
            )
            # Should still succeed since comment was added
            assert "Comment and attachment added successfully" in result[0].text
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
