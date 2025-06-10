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

# Cleanup verification
verify_cleanup() {
    echo "🔍 Verifying cleanup..."
    
    # Check for remaining test containers
    remaining_containers=$(docker ps -a --filter "name=async-code-test-" --filter "name=test-ai-code-task-" -q | wc -l)
    if [ $remaining_containers -gt 0 ]; then
        echo "⚠️  Warning: $remaining_containers test containers still exist"
        docker ps -a --filter "name=async-code-test-" --filter "name=test-ai-code-task-" --format "table {{.Names}}\t{{.Status}}"
    fi
    
    # Check for remaining test volumes
    remaining_volumes=$(docker volume ls --filter "name=async-code-test-" -q | wc -l)
    if [ $remaining_volumes -gt 0 ]; then
        echo "⚠️  Warning: $remaining_volumes test volumes still exist"
        docker volume ls --filter "name=async-code-test-"
    fi
    
    # Check for remaining test networks
    remaining_networks=$(docker network ls --filter "name=async-code-test-" -q | wc -l)
    if [ $remaining_networks -gt 0 ]; then
        echo "⚠️  Warning: $remaining_networks test networks still exist"
        docker network ls --filter "name=async-code-test-"
    fi
}

# Run verification
verify_cleanup

echo "✅ Test environment stopped and cleaned up!"