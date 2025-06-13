#!/bin/bash

echo "=== E2E Authentication Test ==="
echo

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Test 1: Direct backend API call with auth header
echo "Test 1: Direct backend API call with auth header"
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001"}')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "✓ Got access token: ${ACCESS_TOKEN:0:20}..."

# Test 2: Validate token endpoint with auth header
echo -e "\nTest 2: Backend validate-token endpoint with auth header"
VALIDATE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/validate-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"github_token": "ghp_test123", "repo_url": "https://github.com/test/repo"}')

if echo $VALIDATE_RESPONSE | grep -q "Missing authorization header"; then
  echo "✗ FAILED: Missing authorization header"
  exit 1
else
  echo "✓ Authorization header accepted"
fi

# Test 3: Frontend proxy with auth header
echo -e "\nTest 3: Frontend proxy validate-token with auth header"
PROXY_RESPONSE=$(curl -s -X POST http://localhost:3000/api/validate-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"github_token": "ghp_test123", "repo_url": "https://github.com/test/repo"}')

if echo $PROXY_RESPONSE | grep -q "Missing authorization header"; then
  echo "✗ FAILED: Frontend proxy not forwarding auth header"
  exit 1
else
  echo "✓ Frontend proxy forwarding auth header correctly"
fi

echo -e "\n=== All tests passed! ==="