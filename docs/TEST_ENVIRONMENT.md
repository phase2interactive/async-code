# Test Environment Setup

This document describes the isolated test environment for the Async Code project.

## Overview

The test environment provides complete isolation from production systems using:
- Separate Docker Compose configuration (`docker-compose.test.yml`)
- Isolated test database (PostgreSQL on port 5433)
- Separate network (`async-code-test-network`)
- Test-specific environment variables (`.env.test`)
- Dedicated volumes for test data
- Docker-in-Docker for secure container execution
- Automatic credential generation for enhanced security
- Resource limits to prevent excessive consumption
- Kong API Gateway with test-specific configuration

## Quick Start

### First-time Setup
```bash
# Copy example environment files
cp .env.test.example .env.test
cp async-code-web/.env.test.example async-code-web/.env.test

# Update .env.test with your test API keys if needed
```

Note: The test-start.sh script will automatically create these files from examples if they don't exist.

### Starting the Test Environment
```bash
./scripts/test-start.sh
```

This will:
1. Check for conflicting production services
2. Clean up any existing test containers
3. Create .env.test files from examples if they don't exist
4. Build test images
5. Start all test services with health checks
6. Wait for services to be healthy

### Running Tests
```bash
# Run all backend tests
./scripts/test-run.sh pytest

# Run frontend tests
./scripts/test-run.sh frontend

# Run integration tests
./scripts/test-run.sh integration

# Run all tests
./scripts/test-run.sh all

# Run custom command
./scripts/test-run.sh "pytest -k test_specific"
```

### Stopping the Test Environment
```bash
./scripts/test-stop.sh
```

This will prompt whether to remove test data volumes.

## Service Details

### Test Services and Ports
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:5001
- **PostgreSQL**: localhost:5433
- **Kong Admin**: http://localhost:8001

### Container Names
- `async-code-test-db` - PostgreSQL database
- `async-code-test-kong` - API Gateway
- `async-code-test-docker` - Docker-in-Docker service
- `async-code-backend-test` - Backend API
- `async-code-frontend-test` - Frontend application
- `test-ai-code-task-*` - Test task containers

### Volumes
- `async-code-test-postgres-data` - Test database data
- `async-code-test-docker-certs-ca` - Docker TLS CA certificates
- `async-code-test-docker-certs-client` - Docker TLS client certificates

### Networks
- `async-code-test-network` - Isolated bridge network

## Environment Variables

Test-specific variables are defined in:
- `.env.test` - Backend test configuration (auto-generated with secure credentials)
- `async-code-web/.env.test` - Frontend test configuration

Key differences from production:
- `ENVIRONMENT=test`
- `ENABLE_TEST_USERS=true`
- Randomly generated database credentials
- Randomly generated JWT secret
- Different service ports
- Docker-in-Docker configuration for secure container execution

## Health Checks

All services include health checks:
- **Database**: `pg_isready` command
- **Backend**: HTTP GET `/health`
- Services wait for dependencies to be healthy

## Isolation Features

1. **Port Isolation**: Different ports from production (3001, 5001, 5433)
2. **Network Isolation**: Separate Docker network
3. **Volume Isolation**: Separate data volumes
4. **Environment Isolation**: Test-specific configurations
5. **Container Prefix**: Test containers use `test-` prefix
6. **Docker-in-Docker**: Secure container execution without host socket mounting
7. **Resource Limits**: CPU and memory constraints on all containers
8. **Credential Security**: Randomly generated passwords and secrets

## Troubleshooting

### View Logs
```bash
docker-compose -f docker-compose.test.yml logs -f [service-name]
```

### Check Service Status
```bash
docker-compose -f docker-compose.test.yml ps
```

### Manual Cleanup
```bash
# Stop all test containers
docker-compose -f docker-compose.test.yml down -v

# Remove test task containers
docker ps -a --filter "name=test-ai-code-task-" -q | xargs -r docker rm -f
```

## CI/CD Integration

The test environment can be used in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Start Test Environment
  run: ./scripts/test-start.sh

- name: Run Tests
  run: ./scripts/test-run.sh all

- name: Stop Test Environment
  if: always()
  run: ./scripts/test-stop.sh
```