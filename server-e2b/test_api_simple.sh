#!/bin/bash
# Simple API test for E2B backend

echo "🧪 Testing E2B Backend API..."

API_BASE="http://localhost:5000"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test health check
echo -e "\n📋 Testing health endpoints..."
response=$(curl -s "$API_BASE/ping")
if [[ $? -eq 0 ]] && [[ $(echo "$response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✅ /ping endpoint working${NC}"
else
    echo -e "${RED}❌ /ping endpoint failed${NC}"
fi

# Test root endpoint
response=$(curl -s "$API_BASE/")
if [[ $? -eq 0 ]] && [[ $(echo "$response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✅ / (root) endpoint working${NC}"
    echo "   Available endpoints:"
    echo "$response" | jq -r '.endpoints[]' | sed 's/^/   - /'
else
    echo -e "${RED}❌ / (root) endpoint failed${NC}"
fi

# Test authentication without database
echo -e "\n📋 Testing JWT token generation..."
# Generate a test token directly
test_user_id="test-user-$(date +%s)"
response=$(curl -s -X POST "$API_BASE/api/auth/token" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$test_user_id\"}")

if [[ $? -eq 0 ]] && [[ $(echo "$response" | jq -r '.access_token' 2>/dev/null) != "null" ]]; then
    access_token=$(echo "$response" | jq -r '.access_token')
    echo -e "${GREEN}✅ Token generation working${NC}"
    
    # Test token verification
    response=$(curl -s "$API_BASE/api/auth/verify" \
        -H "Authorization: Bearer $access_token")
    
    if [[ $(echo "$response" | jq -r '.valid') == "true" ]]; then
        echo -e "${GREEN}✅ Token verification working${NC}"
    else
        echo -e "${RED}❌ Token verification failed${NC}"
    fi
else
    echo -e "${RED}❌ Token generation failed${NC}"
    echo "Response: $response"
fi

# Test CORS headers
echo -e "\n📋 Testing CORS configuration..."
response_headers=$(curl -s -I -H "Origin: http://localhost:3000" "$API_BASE/ping")
if echo "$response_headers" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ CORS headers present${NC}"
else
    echo -e "${RED}❌ CORS headers missing${NC}"
fi

# Test error handling
echo -e "\n📋 Testing error handling..."
# Test 404
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/nonexistent")
if [[ "$response" == "404" ]]; then
    echo -e "${GREEN}✅ 404 errors handled correctly${NC}"
else
    echo -e "${RED}❌ 404 error handling issue${NC}"
fi

# Summary
echo -e "\n${GREEN}✅ Basic E2B backend tests completed${NC}"
echo -e "\n💡 Note: Full integration tests require:"
echo "  - Valid Supabase credentials"
echo "  - E2B API key (for actual sandbox execution)"
echo "  - GitHub token (for repository operations)"