#!/bin/bash

# Test Environment Teardown Script
# This script stops and cleans up the isolated test environment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🛑 Stopping Async Code Test Environment..."

# Stop services
echo "📦 Stopping test containers..."
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down

# Optional: Remove volumes (prompt user)
read -p "🗑️  Remove test data volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing test volumes..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v
    
    # Remove named volumes explicitly
    docker volume rm async-code-test-postgres-data 2>/dev/null || true
fi

# Clean up any test task containers
echo "🧹 Cleaning up test task containers..."
docker ps -a --filter "name=test-ai-code-task-" -q | xargs -r docker rm -f || true

# Remove test network if it exists
docker network rm async-code-test-network 2>/dev/null || true

echo "✅ Test environment stopped and cleaned up!"