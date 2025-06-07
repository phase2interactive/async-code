#!/bin/bash

echo "🧪 Testing Claude Code Automation API..."

API_BASE="http://localhost:5000"

# Test health check
echo "📋 Testing health check..."
curl -s "$API_BASE/ping" | jq . || echo "❌ Health check failed"

# Test root endpoint
echo "📋 Testing root endpoint..."
curl -s "$API_BASE/" | jq . || echo "❌ Root endpoint failed"

echo ""
echo "✅ Basic API tests completed"
echo "💡 For full testing, you'll need:"
echo "  1. Anthropic API key in server/.env"
echo "  2. GitHub token for task creation"
echo "  3. A target repository URL"