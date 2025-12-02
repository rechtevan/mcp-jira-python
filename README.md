# MCP JIRA Python 🚀

[![CI](https://github.com/rechtevan/mcp-jira-python/actions/workflows/test.yml/badge.svg)](https://github.com/rechtevan/mcp-jira-python/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Python implementation of a MCP server for JIRA integration. MCP is a communication protocol designed to provide tools to your AI and keep your data secure (and local if you like). The server runs on the same computer as your AI application.

**Supports:** Jira Cloud and Jira Server/Data Center (v8.14+)

## Installation

```bash
git clone https://github.com/rechtevan/mcp-jira-python.git
cd mcp-jira-python
pip install -e ".[dev]"
```

## Tools Available (25 tools)

### Issue Management
| Tool | Description |
|------|-------------|
| `create_jira_issue` | Create issues with standard and custom fields |
| `get_issue` | Get issue details including custom fields with friendly names |
| `update_issue` | Update issues with custom field support |
| `delete_issue` | Delete an issue or subtask |
| `search_issues` | Search using JQL |
| `search_my_issues` | Find your assigned/reported issues |

### Workflow & Transitions
| Tool | Description |
|------|-------------|
| `get_transitions` | Get available workflow transitions |
| `transition_issue` | Move issue through workflow states |

### Epic & Hierarchy
| Tool | Description |
|------|-------------|
| `list_epics` | List epics in a project |
| `get_epic_issues` | Get issues under an epic with progress |

### Comments & Attachments
| Tool | Description |
|------|-------------|
| `add_comment` | Add a comment to an issue |
| `add_comment_with_attachment` | Add comment with file attachment |
| `attach_file` | Attach a file to an issue |
| `attach_content` | Create and attach content directly |
| `get_issue_attachment` | Download an attachment |

### Project & Field Discovery
| Tool | Description |
|------|-------------|
| `list_projects` | List accessible projects |
| `list_fields` | Get all available fields |
| `list_issue_types` | Get available issue types |
| `list_link_types` | Get issue link types |
| `get_field_mapping` | Discover custom fields by name |
| `get_create_meta` | Get required fields for issue creation |

### Utilities
| Tool | Description |
|------|-------------|
| `get_user` | Look up user by email |
| `create_issue_link` | Link issues together |
| `format_commit` | Format git commit with Jira reference |

## Configuration

### Environment Variables

Create a `.env.jira` file (or set environment variables):

```bash
# Jira Cloud
JIRA_HOST=your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# OR Jira Server/Data Center (v8.14+)
JIRA_HOST=jira.your-company.com
JIRA_BEARER_TOKEN=your-personal-access-token
```

### Claude Desktop Configuration

**Windows** (`%AppData%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "jira-api": {
      "command": "C:\\Users\\USERNAME\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "D:\\path\\to\\mcp-jira-python",
        "run",
        "-m",
        "mcp_jira_python.server"
      ],
      "env": {
        "JIRA_HOST": "your-domain.atlassian.net",
        "JIRA_EMAIL": "your@email.com",
        "JIRA_API_TOKEN": "your-token"
      }
    }
  }
}
```

**macOS/Linux** (`~/.config/claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "jira-api": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/mcp-jira-python",
        "-m", "mcp_jira_python.server"
      ],
      "env": {
        "JIRA_HOST": "your-domain.atlassian.net",
        "JIRA_EMAIL": "your@email.com",
        "JIRA_API_TOKEN": "your-token"
      }
    }
  }
}
```

> ⚠️ **Note:** Restart Claude Desktop after configuration changes.

### Other MCP Clients

This server works with any MCP client (Cursor, Windsurf, etc.) that supports stdio transport.

## Running Tests

```bash
# Unit tests (no Jira connection needed)
pytest tests/unit_tests/ -v

# With coverage
pytest tests/unit_tests/ --cov=src/mcp_jira_python --cov-report=term

# Integration tests (requires Jira credentials)
pytest tests/integration_tests/ -v
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Run type checking
mypy src/mcp_jira_python

# Run security scan
bandit -r src/ -c pyproject.toml

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
