# E2B Testing Guide

This document provides comprehensive guidance for testing the E2B integration, including environment setup, test execution, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Test Categories](#test-categories)
4. [Running Tests](#running-tests)
5. [Debugging Failed Tests](#debugging-failed-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)

## Overview

The E2B testing suite ensures robust integration with E2B sandboxes for AI code execution. Our tests cover:

- ✅ Sandbox creation and lifecycle management
- ✅ Git operations (clone, commit, patch generation)
- ✅ AI agent execution (Claude and Codex)
- ✅ Error handling and recovery
- ✅ Template configurations
- ✅ Performance characteristics

## Environment Setup

### Required Environment Variables

```bash
# Core E2B Configuration
export E2B_API_KEY="your-e2b-api-key"              # Required for all E2B operations

# AI Agent Keys (at least one required)
export ANTHROPIC_API_KEY="your-anthropic-key"      # Required for Claude agent
export OPENAI_API_KEY="your-openai-key"           # Required for Codex agent

# Optional Configuration
export GITHUB_TOKEN="your-github-token"            # Required for private repos
export E2B_TEMPLATE_ID="your-template-id"          # Optional custom template

# Database Configuration
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

### Local Development Setup

1. **Install Dependencies**
   ```bash
   cd server-e2b
   pip install -r requirements.txt
   pip install -r requirements-test.txt  # Test dependencies
   ```

2. **Create Test Environment File**
   ```bash
   cp .env.example .env.test
   # Edit .env.test with your test credentials
   ```

3. **Verify E2B Access**
   ```bash
   python -c "from e2b import Sandbox; print('E2B OK')"
   ```

## Test Categories

### 1. Unit Tests
Fast, isolated tests that mock E2B interactions:
- `tests/test_e2b_mocked.py` - Core logic without real sandboxes
- `tests/test_error_handling.py` - Error scenarios

### 2. Integration Tests
Tests with real E2B sandboxes (require API key):
- `tests/test_e2b_integration.py` - Basic E2B operations
- `tests/test_e2b_integration_fixtures.py` - Production-like scenarios
- `tests/test_e2b_sandbox_scenarios.py` - Edge cases and error conditions

### 3. Template Tests
- `tests/test_e2b_template_matrix.py` - Different template configurations

### 4. Performance Tests
- `tests/test_e2b_performance.py` - Timing and resource usage

## Running Tests

### Run All Tests
```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=utils --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only (no E2B API required)
pytest -v -m "not integration"

# Integration tests (requires E2B API)
pytest -v -m "integration"

# Specific test file
pytest -v tests/test_e2b_integration.py

# Specific test function
pytest -v tests/test_e2b_integration.py::test_e2b_sandbox_creation
```

### Test Markers
```python
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Requires E2B API
@pytest.mark.slow         # Long-running tests
@pytest.mark.template     # Template-specific tests
```

## Debugging Failed Tests

### 1. Enable Debug Logging
```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
pytest -v -s tests/test_e2b_integration.py

# Or in Python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### 2. Common Issues and Solutions

#### Issue: "E2B_API_KEY not found"
```bash
# Solution: Set the API key
export E2B_API_KEY="your-key"
```

#### Issue: "Template not found"
```python
# Solution: Use fallback to default template
try:
    sandbox = Sandbox(template=template_id)
except NotFoundException:
    sandbox = Sandbox()  # Use default
```

#### Issue: "/workspace directory not found"
```python
# Solution: Create directory before operations
sandbox.commands.run("mkdir -p /workspace")
```

#### Issue: "Git clone timeout"
```python
# Solution: Increase timeout or use smaller repo
CLONE_TIMEOUT = 120  # Increase from 60
```

### 3. Inspecting Failed Sandboxes
```python
# Keep sandbox alive for debugging
sandbox = Sandbox(timeout=3600)  # 1 hour
print(f"Sandbox ID: {sandbox.id}")
# Debug in sandbox...
input("Press Enter to cleanup...")
sandbox.kill()
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2B Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: pytest -v -m "not integration"
    
    - name: Run integration tests
      if: github.event_name == 'push'
      env:
        E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      run: pytest -v -m "integration"
```

### Test Environment Isolation
```bash
# Use separate E2B account for testing
export E2B_API_KEY="test-account-key"

# Use test-specific template
export E2B_TEMPLATE_ID="test-template-v1"
```

## Best Practices

### 1. Test Data Management
```python
# Use small, predictable test repositories
TEST_REPOS = {
    "small": "https://github.com/octocat/Hello-World.git",
    "medium": "https://github.com/github/docs.git",
    "large": "https://github.com/torvalds/linux.git"  # Use sparingly
}
```

### 2. Resource Cleanup
```python
@pytest.fixture
async def sandbox():
    """Ensure sandbox cleanup even on test failure"""
    sandbox = None
    try:
        sandbox = await create_sandbox()
        yield sandbox
    finally:
        if sandbox:
            sandbox.kill()
```

### 3. Mock vs Real Tests
```python
# Use mocks for logic testing
@patch('e2b.Sandbox')
def test_logic_with_mock(mock_sandbox):
    # Fast, reliable, no API calls
    pass

# Use real sandboxes sparingly
@pytest.mark.integration
async def test_with_real_sandbox():
    # Slower, requires API, more realistic
    pass
```

### 4. Timeout Management
```python
# Set appropriate timeouts
TIMEOUTS = {
    "command": 30,      # Regular commands
    "clone": 60,        # Git clone
    "agent": 300,       # AI agent execution
    "sandbox": 600,     # Total sandbox lifetime
}
```

### 5. Error Message Sanitization
```python
def test_error_sanitization():
    """Ensure secrets don't leak in errors"""
    error = "Failed with token: ghp_secret123"
    sanitized = sanitize_error(error)
    assert "ghp_secret123" not in sanitized
    assert "***" in sanitized
```

## Test Coverage Goals

- **Unit Tests**: >90% coverage of core logic
- **Integration Tests**: Cover all critical paths
- **Error Handling**: Test all exception scenarios
- **Templates**: Test at least 3 different configurations
- **Performance**: Baseline metrics for regression detection

## Troubleshooting

### Running Individual Tests in VS Code
1. Install Python Test Explorer extension
2. Configure in `.vscode/settings.json`:
   ```json
   {
     "python.testing.pytestArgs": [
       "tests",
       "-v"
     ],
     "python.testing.unittestEnabled": false,
     "python.testing.pytestEnabled": true
   }
   ```

### Debugging E2B Sandbox Issues
```python
# Enable E2B debug logging
import logging
logging.getLogger("e2b").setLevel(logging.DEBUG)

# Inspect sandbox state
result = sandbox.commands.run("env")
print("Environment:", result.stdout)

result = sandbox.commands.run("ls -la /")
print("Root filesystem:", result.stdout)
```

### Common Test Failures

1. **Quota Exceeded**
   - Check E2B dashboard for usage
   - Consider using mock tests more
   - Implement test throttling

2. **Network Timeouts**
   - Increase timeout values
   - Check network connectivity
   - Use local test data when possible

3. **Template Not Found**
   - Verify template ID is correct
   - Implement fallback to default
   - Cache template availability

## Contributing

When adding new tests:

1. Follow existing patterns
2. Add appropriate markers
3. Document special requirements
4. Update this guide if needed
5. Ensure tests pass locally before PR

For questions or issues, please refer to the [E2B documentation](https://e2b.dev/docs) or open an issue in the repository.