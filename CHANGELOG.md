# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-02

### Added
- **26 Jira tools** for comprehensive Jira integration via MCP
- **Issue Management**: create, get, update, delete, search issues
- **Workflow & Transitions**: get available transitions, transition issues through workflow states
- **Epic & Hierarchy**: list epics, get epic issues with progress tracking
- **Comments & Attachments**: add comments, attach files, download attachments
- **Project & Field Discovery**: list projects, fields, issue types, link types, field mappings
- **Quality & Guidance**: audit issues for completeness, suggest fields for issue creation
- **Utilities**: get user by email, create issue links, format git commits with Jira references
- **Custom field support**: Friendly names for custom fields (e.g., "Story Points" instead of "customfield_10002")
- **Dual authentication**: Support for Jira Cloud (email + API token) and Jira Data Center (bearer token/PAT)
- **MCP runner compatibility**: Server now uses absolute path to find `.env.jira` relative to the script location, ensuring it works with Cursor and other MCP clients regardless of working directory
- **Comprehensive test suite**: 32+ unit tests with mocked Jira connections
- **Pre-commit hooks**: Ruff linting, formatting, mypy type checking, bandit security scanning
- **GitHub Actions CI/CD**: Automated testing on push and pull requests

### Removed
- Removed outdated `TEST_RESULTS.md` - test results now come from CI/CD and pytest output

## [0.1.0] - 2025-11-12

### Added
- Initial fork from original repository
- Basic MCP server structure
- Core Jira connectivity

### Notes
- Supports Jira Cloud and Jira Server/Data Center (v8.14+)
