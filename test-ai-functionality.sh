#!/bin/bash

echo "🤖 Testing AI agent functionality with secure containers..."
echo ""

# Create a test repository
TEST_DIR="/tmp/test-ai-repo-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize git repo
git init
echo "# Test Repository" > README.md
git add README.md
git config user.email "test@example.com"
git config user.name "Test User"
git commit -m "Initial commit"

echo "📁 Created test repository at: $TEST_DIR"
echo ""

# Test Claude container
echo "1️⃣ Testing Claude Code in secure container..."
docker run --rm \
    --user 1000:1000 \
    --security-opt no-new-privileges=true \
    -v "$TEST_DIR:/workspace/repo" \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-test}" \
    claude-code-automation:latest \
    bash -c "cd /workspace/repo && echo 'Test prompt' > /tmp/prompt.txt && echo 'Claude container can execute commands successfully'"

echo ""

# Test Codex container
echo "2️⃣ Testing Codex in secure container..."
docker run --rm \
    --user 1000:1000 \
    --security-opt no-new-privileges=true \
    -v "$TEST_DIR:/workspace/repo" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-test}" \
    codex-automation:latest \
    bash -c "cd /workspace/repo && echo 'Test prompt' > /tmp/prompt.txt && echo 'Codex container can execute commands successfully'"

echo ""

# Test git operations
echo "3️⃣ Testing git operations in secure container..."
docker run --rm \
    --user 1000:1000 \
    --security-opt no-new-privileges=true \
    -v "$TEST_DIR:/workspace/repo" \
    claude-code-automation:latest \
    bash -c "cd /workspace/repo && git status && echo 'Git operations work correctly'"

echo ""

# Cleanup
rm -rf "$TEST_DIR"

echo "✅ AI functionality tests completed!"
echo ""
echo "Note: For full integration testing with actual AI models, ensure API keys are set and run the full task execution flow."