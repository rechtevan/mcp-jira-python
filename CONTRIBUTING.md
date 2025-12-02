# Contributing to mcp-jira-python

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/rechtevan/mcp-jira-python.git
cd mcp-jira-python

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Branching Strategy (Gitflow)

We use a simplified Gitflow branching model:

### Branch Types

| Branch | Purpose | Base |
|--------|---------|------|
| `main` | Production-ready releases | - |
| `develop` | Integration branch | main |
| `feature/*` | New features | develop |
| `bugfix/*` | Bug fixes | develop |
| `hotfix/*` | Emergency production fixes | main |
| `release/*` | Release preparation | develop |

### Branch Naming Convention

```
feature/short-description
feature/PROJ-123-add-epic-tools
bugfix/fix-auth-error
hotfix/critical-security-fix
release/v1.2.0
```

### Workflow

1. **Features**: Branch from `develop`, PR back to `develop`
2. **Releases**: Branch from `develop`, merge to both `main` and `develop`
3. **Hotfixes**: Branch from `main`, merge to both `main` and `develop`

## Code Quality

Before submitting a PR, ensure:

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/mcp_jira_python

# Security scan
bandit -r src/ -c pyproject.toml

# Run tests with coverage
pytest tests/unit_tests/ --cov=src/mcp_jira_python --cov-report=term
```

Or run all checks via pre-commit:
```bash
pre-commit run --all-files
```

## Testing

- **Unit tests**: `tests/unit_tests/` - Mocked, no Jira connection needed
- **Integration tests**: `tests/integration_tests/` - Require Jira credentials
- **E2E tests**: `tests/e2e_tests/` - Full MCP server tests

Coverage requirement: **90%** minimum

## Pull Request Guidelines

1. Create a feature branch from `develop`
2. Write tests for new functionality
3. Ensure all checks pass
4. Update documentation if needed
5. Submit PR to `develop` (or `main` for hotfixes)

## Commit Message Format

Include Jira issue key when applicable:

```
PROJ-123: Add epic listing tool

- Implement list_epics tool
- Add get_epic_issues for hierarchy
- Update README with new tools
```

For non-Jira tracked work:
```
fix: correct type hints in field_mapper

docs: update README with installation steps
```

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.



