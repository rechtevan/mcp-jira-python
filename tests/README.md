# MCP JIRA Python Tests

This directory contains the test suite for the MCP JIRA Python server.

## Test Categories

| Category | Marker | Description | Jira Required |
|----------|--------|-------------|---------------|
| **Unit** | `@pytest.mark.unit` | Fast tests with mocked dependencies | No |
| **Integration** | `@pytest.mark.integration` | Tests against real Jira | Yes |
| **E2E** | `@pytest.mark.e2e` | Full MCP server flow tests | Some |

## Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── unit_tests/              # Unit tests (mocked, fast)
│   ├── test_get_issue.py
│   ├── test_create_issue.py
│   └── ...
├── integration_tests/       # Integration tests (requires Jira)
│   └── ...
├── e2e_tests/               # End-to-end tests
│   └── test_mcp_server.py
└── endpoint_tests/          # Legacy endpoint tests
```

## Running Tests

### With pytest (recommended)

```bash
# Run all tests
pytest

# Run only unit tests (fast, no Jira needed)
pytest -m unit

# Run only integration tests (requires Jira)
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Run with coverage
pytest --cov=src/mcp_jira_python --cov-report=term-missing --cov-report=html

# Run with coverage and fail if below threshold
pytest --cov=src/mcp_jira_python --cov-fail-under=90
```

### With unittest (legacy)

```bash
python -m unittest discover tests
python -m unittest discover tests/unit_tests
```

## Environment Setup

### For Integration/E2E Tests

Create a `.env` file in the tests directory or use environment variables:

```bash
# Jira Server/Data Center (with PAT)
export JIRA_HOST="jira.yourcompany.com"
export JIRA_BEARER_TOKEN="your_pat_token"
export JIRA_PROJECT_KEY="TEST"

# OR Jira Cloud
export JIRA_HOST="yourcompany.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your_api_token"
export JIRA_PROJECT_KEY="TEST"
```

## Coverage Standards

| Scope | Minimum |
|-------|---------|
| **Overall** | 90% |
| Per module | 80% |
| Per class | 80% |
| Per function | 80% |

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock
from mcp_jira_python.tools.get_issue import GetIssueTool

@pytest.mark.unit
class TestGetIssueTool:
    def test_execute_returns_issue_data(self, mock_jira, mock_issue):
        tool = GetIssueTool()
        tool.jira = mock_jira
        mock_jira.issue.return_value = mock_issue

        result = asyncio.run(tool.execute({"issueKey": "TEST-123"}))

        assert result[0].type == "text"
        assert "TEST-123" in result[0].text
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
class TestJiraIntegration:
    def test_search_issues(self, jira_client, test_project_key):
        issues = jira_client.search_issues(f"project = {test_project_key}")
        assert issues is not None
```

## Fixtures

Key fixtures defined in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `mock_jira` | Mock Jira client for unit tests |
| `mock_issue` | Mock issue with standard fields |
| `jira_client` | Real Jira client (integration tests) |
| `test_project_key` | Project key from env or "TEST" |
| `requires_jira` | Skip if Jira not configured |
