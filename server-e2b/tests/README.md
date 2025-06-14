# Test Suite

This directory contains all tests for the E2B server implementation.

## Test Structure

```
tests/
├── README.md                          # This file
├── __init__.py                        # Makes tests a Python package
│
├── test_e2b_integration.py           # E2B integration tests (requires API key)
├── test_e2b_unit.py                  # Unit tests for E2B functionality
├── test_e2b_sandbox_scenarios.py     # Comprehensive sandbox scenario tests
├── test_e2b_integration_fixtures.py  # Reusable test fixtures
├── test_e2b_template_matrix.py       # Template configuration tests
├── test_e2b_backend.py               # Backend E2B tests
├── test_e2b_mode.py                  # E2B mode tests
│
├── test_backend.py                   # General backend tests
├── test_auth_header.py               # Authentication header tests
├── test_integration_auth.py          # Auth integration tests
├── test_users.py                     # User management tests
├── test_user_service.py              # User service tests
├── test_user_models.py               # User model tests
│
└── utils/
    └── agent_scripts/
        ├── __init__.py
        ├── test_claude_agent.py      # Claude agent tests
        ├── test_codex_agent.py       # Codex agent tests
        └── test_parser_utils.py      # Parser utility tests
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only (no external dependencies)
pytest -m "not integration"

# Integration tests (requires E2B API key)
pytest -m integration

# E2B specific tests
pytest -m e2b

# Run a specific test file
pytest tests/test_e2b_integration.py

# Run with coverage
pytest --cov=utils --cov-report=html
```

### Run integration tests directly
```bash
# Some integration tests can be run as scripts
python tests/test_e2b_integration.py
```

## Test Categories

- **Unit Tests**: Fast tests that mock external dependencies
- **Integration Tests**: Tests that require real E2B API access
- **Fixture Tests**: Reusable test components
- **Scenario Tests**: Comprehensive edge case testing

## Environment Variables

For integration tests, ensure these are set:
```bash
export E2B_API_KEY="your-e2b-api-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GITHUB_TOKEN="your-github-token"
```

## Writing New Tests

1. Place test files in the appropriate directory
2. Name test files with `test_` prefix
3. Use pytest markers to categorize tests:
   ```python
   @pytest.mark.unit
   @pytest.mark.integration
   @pytest.mark.e2b
   ```
4. Use the fixtures from `test_e2b_integration_fixtures.py` for consistent test setup