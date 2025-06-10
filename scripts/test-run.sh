#!/bin/bash

# Test Runner Script
# This script runs tests in the isolated test environment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default test command
TEST_CMD="${1:-pytest}"

echo "🧪 Running Tests in Isolated Environment..."

# Check if test environment is running
if ! docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" ps | grep -q "Up"; then
    echo "❌ Test environment is not running!"
    echo "   Start it with: ./scripts/test-start.sh"
    exit 1
fi

# Run tests based on the service
case "$TEST_CMD" in
    pytest|backend)
        echo "🐍 Running backend tests..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T backend-test pytest -v
        ;;
    jest|frontend)
        echo "⚛️  Running frontend tests..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T frontend-test npm test
        ;;
    integration)
        echo "🔗 Running integration tests..."
        # Run backend integration tests
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T backend-test pytest -v tests/integration/
        ;;
    all)
        echo "🎯 Running all tests..."
        # Run backend tests
        echo "🐍 Backend tests:"
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T backend-test pytest -v
        
        # Run frontend tests
        echo "⚛️  Frontend tests:"
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T frontend-test npm test || true
        ;;
    *)
        echo "📝 Custom test command: $TEST_CMD"
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec -T backend-test $TEST_CMD
        ;;
esac

echo "✅ Tests completed!"