"""Unit tests for GetIssueAttachmentTool."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_jira_python.tools.get_issue_attachment import GetIssueAttachmentTool


@pytest.fixture
def mock_attachment() -> Mock:
    """Mock attachment."""
    attachment = Mock()
    attachment.id = "12345"
    attachment.filename = "test.txt"
    attachment.size = 17
    attachment.get.return_value = b"Test file content"
    return attachment


@pytest.fixture
def mock_jira(mock_attachment: Mock) -> Mock:
    """Create mock Jira client."""
    jira = Mock()
    jira.attachment.return_value = mock_attachment
    return jira


@pytest.fixture
def tool(mock_jira: Mock) -> GetIssueAttachmentTool:
    """Create tool with mock Jira."""
    tool = GetIssueAttachmentTool()
    tool.jira = mock_jira
    return tool


@pytest.mark.unit
class TestGetIssueAttachmentTool:
    """Tests for GetIssueAttachmentTool."""

    def test_execute_by_attachment_id(self, tool: GetIssueAttachmentTool, mock_jira: Mock) -> None:
        """Test downloading attachment by attachment ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "attachmentId": "12345",
                        "outputPath": tmpdir,
                    }
                )
            )

            assert result[0].type == "text"
            assert "downloaded successfully" in result[0].text.lower()
            assert "test.txt" in result[0].text

            mock_jira.attachment.assert_called_once_with("12345")

            expected_path = Path(tmpdir) / "test.txt"
            assert expected_path.exists()

    def test_execute_by_filename(
        self, tool: GetIssueAttachmentTool, mock_jira: Mock, mock_attachment: Mock
    ) -> None:
        """Test downloading attachment by filename."""
        mock_issue = Mock()
        mock_issue.fields.attachment = [mock_attachment]
        mock_jira.issue.return_value = mock_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            result = asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "filename": "test.txt",
                        "outputPath": tmpdir,
                    }
                )
            )

            assert result[0].type == "text"
            assert "downloaded successfully" in result[0].text.lower()
            mock_jira.issue.assert_called_once()

    def test_execute_download_all(
        self, tool: GetIssueAttachmentTool, mock_jira: Mock, mock_attachment: Mock
    ) -> None:
        """Test downloading all attachments."""
        mock_attachment2 = Mock()
        mock_attachment2.id = "67890"
        mock_attachment2.filename = "test2.txt"
        mock_attachment2.size = 100
        mock_attachment2.get.return_value = b"Second file content"

        mock_issue = Mock()
        mock_issue.fields.attachment = [mock_attachment, mock_attachment2]
        mock_jira.issue.return_value = mock_issue

        with tempfile.TemporaryDirectory() as tmpdir:
            result = asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "outputPath": tmpdir,
                    }
                )
            )

            assert result[0].type == "text"
            assert "2" in result[0].text
            assert "attachments" in result[0].text.lower()

            assert (Path(tmpdir) / "test.txt").exists()
            assert (Path(tmpdir) / "test2.txt").exists()

    def test_execute_missing_issue_key(self, tool: GetIssueAttachmentTool) -> None:
        """Test error handling for missing issue key."""
        with pytest.raises(ValueError, match="required"):
            asyncio.run(tool.execute({"attachmentId": "12345"}))

    def test_execute_no_attachments_found(
        self, tool: GetIssueAttachmentTool, mock_jira: Mock
    ) -> None:
        """Test error handling when issue has no attachments."""
        mock_issue = Mock()
        mock_issue.fields.attachment = []
        mock_jira.issue.return_value = mock_issue

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            pytest.raises(Exception, match=r"(?i)no attachments"),
        ):
            asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "filename": "test.txt",
                        "outputPath": tmpdir,
                    }
                )
            )

    def test_execute_filename_not_found(
        self, tool: GetIssueAttachmentTool, mock_jira: Mock
    ) -> None:
        """Test error handling when specified filename is not found."""
        other_attachment = Mock()
        other_attachment.filename = "other.txt"
        other_attachment.size = 100
        other_attachment.get.return_value = b"other content"

        mock_issue = Mock()
        mock_issue.fields.attachment = [other_attachment]
        mock_jira.issue.return_value = mock_issue

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            pytest.raises(Exception, match="not found"),
        ):
            asyncio.run(
                tool.execute(
                    {
                        "issueKey": "TEST-123",
                        "filename": "test.txt",
                        "outputPath": tmpdir,
                    }
                )
            )

    def test_tool_definition(self, tool: GetIssueAttachmentTool) -> None:
        """Test tool definition."""
        definition = tool.get_tool_definition()
        assert definition.name == "get_issue_attachment"
        assert "issueKey" in definition.inputSchema["properties"]
