#!/bin/bash
# Build and publish the custom E2B template

set -e

echo "🔨 Building custom E2B template for async-code agents..."

# Check if E2B CLI is installed
if ! command -v e2b &> /dev/null; then
    echo "❌ E2B CLI not found. Installing..."
    npm install -g @e2b/cli
fi

# Build the template
echo "📦 Building template..."
e2b template build

# Get the template ID
TEMPLATE_ID=$(e2b template list | grep "async-code-agents" | awk '{print $1}')

if [ -z "$TEMPLATE_ID" ]; then
    echo "❌ Failed to build template"
    exit 1
fi

echo "✅ Template built successfully!"
echo "📝 Template ID: $TEMPLATE_ID"
echo ""
echo "To use this template, update code_task_e2b_real.py:"
echo "  await Sandbox.create(template='$TEMPLATE_ID', ...)"