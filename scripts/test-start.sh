#!/bin/bash

# Test Environment Startup Script
# This script starts the isolated test environment for async-code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Async Code Test Environment..."

# Check if production services are running
if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
    echo "⚠️  Warning: Production services are running. This may cause port conflicts."
    echo "   Consider stopping them with: docker-compose down"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted."
        exit 1
    fi
fi

# Clean up any existing test containers
echo "🧹 Cleaning up existing test containers..."
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v --remove-orphans || true

# Remove any dangling test containers
docker ps -a --filter "name=async-code-test-" --filter "name=test-ai-code-task-" -q | xargs -r docker rm -f || true

# Check if .env.test exists
if [ ! -f "$PROJECT_ROOT/.env.test" ]; then
    echo "📝 Creating .env.test from .env.test.example..."
    cp "$PROJECT_ROOT/.env.test.example" "$PROJECT_ROOT/.env.test"
    echo "   Please update .env.test with your test API keys if needed."
fi

# Check if frontend .env.test exists
if [ ! -f "$PROJECT_ROOT/async-code-web/.env.test" ]; then
    echo "📝 Creating async-code-web/.env.test from .env.test.example..."
    cp "$PROJECT_ROOT/async-code-web/.env.test.example" "$PROJECT_ROOT/async-code-web/.env.test"
fi

# Build images
echo "🔨 Building test images..."
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" build

# Start services
echo "🚀 Starting test services..."
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" ps | grep -q "unhealthy\|starting"; then
        echo -n "."
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    else
        echo
        break
    fi
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo
    echo "❌ Services failed to become healthy within $TIMEOUT seconds"
    docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" ps
    exit 1
fi

# Show service status
echo
echo "✅ Test environment is ready!"
echo
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" ps

echo
echo "📍 Test Service URLs:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:5001"
echo "   - Database: postgresql://test_user:test_password@localhost:5433/test_db"
echo "   - Kong Admin: http://localhost:8001"
echo
echo "📝 View logs: docker-compose -f docker-compose.test.yml logs -f"
echo "🛑 Stop services: ./scripts/test-stop.sh"