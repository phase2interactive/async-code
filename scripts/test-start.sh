#!/bin/bash

# Test Environment Startup Script
# This script starts the isolated test environment for async-code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to generate secure random credentials
generate_test_credentials() {
    echo "🔐 Generating secure test credentials..."
    
    # Generate random passwords and secrets
    TEST_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    TEST_JWT_SECRET=$(openssl rand -base64 32)
    TEST_SUPABASE_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    # Export for use in docker-compose
    export TEST_DB_PASSWORD
    export TEST_JWT_SECRET
    export TEST_SUPABASE_KEY
}

echo "🚀 Starting Async Code Test Environment..."

# Check dependencies
check_dependencies() {
    echo "🔧 Checking dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Error: Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Error: Docker Compose is not installed"
        exit 1
    fi
    
    # Check Docker Compose version
    compose_version=$(docker-compose version --short 2>/dev/null || echo "0.0.0")
    major_version=$(echo "$compose_version" | cut -d. -f1)
    minor_version=$(echo "$compose_version" | cut -d. -f2)
    
    if [ "$major_version" -lt 1 ] || ([ "$major_version" -eq 1 ] && [ "$minor_version" -lt 27 ]); then
        echo "⚠️  Warning: Docker Compose version $compose_version detected"
        echo "   Recommended version is 1.27.0 or higher for full feature support"
    fi
    
    # Check OpenSSL for credential generation
    if ! command -v openssl &> /dev/null; then
        echo "❌ Error: OpenSSL is not installed (required for credential generation)"
        exit 1
    fi
    
    echo "✅ All dependencies satisfied"
}

# Run dependency check
check_dependencies

# Enhanced production service check
check_production_services() {
    echo "🔍 Checking for conflicting services..."
    
    # Check if production docker-compose file exists
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        return 0
    fi
    
    # Get list of running production services
    prod_services=$(docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps --services 2>/dev/null || true)
    
    if [ -n "$prod_services" ]; then
        echo "⚠️  Warning: Production services are running:"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps
        echo
        
        # Check for specific port conflicts
        conflicts=0
        for port in 3001 5001 5433 8000 8001; do
            if lsof -i :$port >/dev/null 2>&1 || netstat -tln 2>/dev/null | grep -q ":$port "; then
                echo "   ❌ Port $port is already in use"
                conflicts=$((conflicts + 1))
            fi
        done
        
        if [ $conflicts -gt 0 ]; then
            echo
            echo "   Port conflicts detected. You can:"
            echo "   1. Stop production services: docker-compose down"
            echo "   2. Modify test ports in docker-compose.test.yml"
            echo
            read -p "   Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "❌ Aborted."
                exit 1
            fi
        fi
    fi
}

# Run production check
check_production_services

# Clean up any existing test containers
echo "🧹 Cleaning up existing test containers..."
docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v --remove-orphans || true

# Remove any dangling test containers
docker ps -a --filter "name=async-code-test-" --filter "name=test-ai-code-task-" -q | xargs -r docker rm -f || true

# Generate credentials
generate_test_credentials

# Check if .env.test exists
if [ ! -f "$PROJECT_ROOT/.env.test" ]; then
    echo "📝 Creating .env.test with secure credentials..."
    cat > "$PROJECT_ROOT/.env.test" << EOF
# Test Environment Configuration - Generated $(date)
ENVIRONMENT="test"
ENABLE_TEST_USERS="true"

# Test Database Configuration (Generated)
DATABASE_URL="postgresql://test_user:${TEST_DB_PASSWORD}@test-db:5432/test_db"
SUPABASE_URL="http://test-kong:8000"
SUPABASE_KEY="${TEST_SUPABASE_KEY}"
SUPABASE_SERVICE_KEY="${TEST_SUPABASE_KEY}"

# Test JWT Configuration (Generated)
JWT_SECRET="${TEST_JWT_SECRET}"

# Test API Keys (Replace with test keys if available)
ANTHROPIC_API_KEY="\${ANTHROPIC_API_KEY:-test-anthropic-key}"
PERPLEXITY_API_KEY="\${PERPLEXITY_API_KEY:-test-perplexity-key}"
OPENAI_API_KEY="\${OPENAI_API_KEY:-test-openai-key}"
GOOGLE_API_KEY="\${GOOGLE_API_KEY:-test-google-key}"
MISTRAL_API_KEY="\${MISTRAL_API_KEY:-test-mistral-key}"
XAI_API_KEY="\${XAI_API_KEY:-test-xai-key}"
AZURE_OPENAI_API_KEY="\${AZURE_OPENAI_API_KEY:-test-azure-key}"
OLLAMA_API_KEY="\${OLLAMA_API_KEY:-test-ollama-key}"

# Test API Configuration
API_BASE_URL="http://backend-test:5000"
FRONTEND_URL="http://frontend-test:3000"

# Test-specific settings
TEST_MODE="true"
LOG_LEVEL="DEBUG"
MAX_TEST_CONTAINERS="5"
TEST_CONTAINER_PREFIX="test-ai-code-task"
TEST_TIMEOUT_SECONDS="300"

# Generated credentials
TEST_DB_PASSWORD="${TEST_DB_PASSWORD}"
EOF
    echo "   Test credentials have been generated and saved."
else
    echo "📝 Using existing .env.test file..."
    # Source the existing file to get credentials
    source "$PROJECT_ROOT/.env.test"
fi

# Check if frontend .env.test exists
if [ ! -f "$PROJECT_ROOT/async-code-web/.env.test" ]; then
    echo "📝 Creating async-code-web/.env.test..."
    cat > "$PROJECT_ROOT/async-code-web/.env.test" << EOF
# Test Frontend Configuration - Generated $(date)
NEXT_PUBLIC_SUPABASE_URL="http://localhost:8000"
NEXT_PUBLIC_SUPABASE_ANON_KEY="${TEST_SUPABASE_KEY}"
NEXT_PUBLIC_API_URL="http://localhost:5001"
NEXT_PUBLIC_ENVIRONMENT="test"
EOF
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