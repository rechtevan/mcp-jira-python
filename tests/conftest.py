"""Pytest configuration and fixtures for mcp-jira-python tests.

Test Categories:
- unit: Fast tests with mocked dependencies (no Jira connection)
- integration: Tests that require a real Jira connection
- e2e: End-to-end tests that test the full MCP server flow
"""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

# Load test environment variables
test_env = Path(__file__).parent / ".env"
if test_env.exists():
    load_dotenv(test_env)
else:
    # Try project root .env.jira
    project_env = Path(__file__).parent.parent / ".env.jira"
    if project_env.exists():
        load_dotenv(project_env)


# =============================================================================
# Pytest Markers
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (mocked, fast)")
    config.addinivalue_line("markers", "integration: Integration tests (requires Jira)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full MCP flow)")
    config.addinivalue_line("markers", "slow: Slow tests")


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def jira_host() -> str | None:
    """Get Jira host from environment."""
    return os.getenv("JIRA_HOST")


@pytest.fixture
def jira_credentials() -> dict[str, str | None]:
    """Get Jira credentials from environment."""
    return {
        "host": os.getenv("JIRA_HOST"),
        "email": os.getenv("JIRA_EMAIL"),
        "api_token": os.getenv("JIRA_API_TOKEN"),
        "bearer_token": os.getenv("JIRA_BEARER_TOKEN"),
    }


@pytest.fixture
def requires_jira(jira_credentials: dict[str, str | None]) -> None:
    """Skip test if Jira credentials are not available."""
    if not jira_credentials["host"]:
        pytest.skip("JIRA_HOST not set")
    if not jira_credentials["bearer_token"] and not (
        jira_credentials["email"] and jira_credentials["api_token"]
    ):
        pytest.skip("Jira credentials not set")


# =============================================================================
# Mock Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_jira() -> Mock:
    """Create a mock Jira client."""
    return Mock()


@pytest.fixture
def mock_issue() -> Mock:
    """Create a mock Jira issue."""
    issue = Mock()
    issue.key = "TEST-123"
    issue.id = "12345"
    issue.self = "https://jira.example.com/rest/api/2/issue/12345"

    # Fields
    issue.fields = Mock()
    issue.fields.summary = "Test Issue Summary"
    issue.fields.description = "Test Issue Description"
    issue.fields.status = Mock()
    issue.fields.status.name = "Open"
    issue.fields.status.__str__ = lambda self: "Open"
    issue.fields.priority = Mock()
    issue.fields.priority.name = "High"
    issue.fields.priority.__str__ = lambda self: "High"
    issue.fields.assignee = Mock()
    issue.fields.assignee.displayName = "Test User"
    issue.fields.assignee.__str__ = lambda self: "Test User"
    issue.fields.issuetype = Mock()
    issue.fields.issuetype.name = "Task"
    issue.fields.issuetype.__str__ = lambda self: "Task"

    # Comments
    mock_comment = Mock()
    mock_comment.id = "10001"
    mock_comment.author = Mock()
    mock_comment.author.__str__ = lambda self: "Comment Author"
    mock_comment.body = "Test comment body"
    mock_comment.created = "2024-01-30T12:00:00.000+0000"
    issue.fields.comment = Mock()
    issue.fields.comment.comments = [mock_comment]

    # Attachments
    mock_attachment = Mock()
    mock_attachment.id = "20001"
    mock_attachment.filename = "test_file.txt"
    mock_attachment.size = 1024
    mock_attachment.created = "2024-01-30T12:00:00.000+0000"
    issue.fields.attachment = [mock_attachment]

    return issue


@pytest.fixture
def mock_comment() -> Mock:
    """Create a mock Jira comment."""
    comment = Mock()
    comment.id = "10001"
    comment.author = Mock()
    comment.author.__str__ = lambda self: "Comment Author"
    comment.body = "Test comment"
    comment.created = "2024-01-30T12:00:00.000+0000"
    return comment


# =============================================================================
# Tool Fixtures
# =============================================================================


@pytest.fixture
def sample_issue_data() -> dict[str, Any]:
    """Sample data for creating an issue."""
    return {
        "projectKey": "TEST",
        "summary": "Test Issue from pytest",
        "issueType": "Task",
        "description": "This is a test issue created by pytest",
    }


@pytest.fixture
def sample_comment_data() -> dict[str, str]:
    """Sample data for adding a comment."""
    return {
        "issueKey": "TEST-123",
        "comment": "Test comment from pytest",
    }


# =============================================================================
# Integration Test Fixtures
# =============================================================================


@pytest.fixture
def jira_client(requires_jira: None, jira_credentials: dict[str, str | None]) -> Generator[Any, None, None]:
    """Create a real Jira client for integration tests."""
    from jira import JIRA

    host = jira_credentials["host"]
    if not host:
        pytest.skip("JIRA_HOST not set")

    # Build URL
    if host.startswith("http://") or host.startswith("https://"):
        server_url = host
    else:
        server_url = f"https://{host}"

    # Connect with available auth
    if jira_credentials["bearer_token"]:
        client = JIRA(server=server_url, token_auth=jira_credentials["bearer_token"])
    elif jira_credentials["email"] and jira_credentials["api_token"]:
        client = JIRA(
            server=server_url,
            basic_auth=(jira_credentials["email"], jira_credentials["api_token"]),
        )
    else:
        pytest.skip("No valid Jira credentials")

    yield client


@pytest.fixture
def test_project_key() -> str:
    """Get test project key from environment or use default."""
    return os.getenv("JIRA_PROJECT_KEY", "TEST")
