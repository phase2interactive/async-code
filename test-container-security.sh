#!/bin/bash

echo "🔒 Testing container security restrictions..."
echo ""

# Test 1: Verify containers run as non-root user
echo "1️⃣ Testing non-root user execution..."
docker run --rm claude-code-automation:latest bash -c "id"
docker run --rm codex-automation:latest bash -c "id"
echo ""

# Test 2: Verify containers cannot access host PID namespace
echo "2️⃣ Testing PID namespace isolation..."
docker run --rm claude-code-automation:latest bash -c "ps aux | head -10"
echo ""

# Test 3: Verify containers cannot modify protected system files
echo "3️⃣ Testing file system restrictions..."
docker run --rm claude-code-automation:latest bash -c "touch /etc/test 2>&1 || echo 'PASS: Cannot write to /etc'"
docker run --rm claude-code-automation:latest bash -c "touch /usr/test 2>&1 || echo 'PASS: Cannot write to /usr'"
echo ""

# Test 4: Verify no-new-privileges security option
echo "4️⃣ Testing privilege escalation prevention..."
docker run --rm --security-opt no-new-privileges=true claude-code-automation:latest bash -c "su root 2>&1 || echo 'PASS: Cannot escalate privileges'"
echo ""

# Test 5: Verify workspace is writable
echo "5️⃣ Testing workspace write permissions..."
docker run --rm --user 1000:1000 claude-code-automation:latest bash -c "touch /workspace/test.txt && echo 'PASS: Can write to workspace' && rm /workspace/test.txt"
docker run --rm --user 1000:1000 codex-automation:latest bash -c "touch /workspace/test.txt && echo 'PASS: Can write to workspace' && rm /workspace/test.txt"
echo ""

echo "✅ Security tests completed!"