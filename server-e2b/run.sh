#!/bin/bash
# Run script for E2B backend

echo "🚀 Starting E2B Backend..."

# Export environment variables
export FLASK_ENV=${FLASK_ENV:-development}
export PORT=${PORT:-5000}
export E2B_ENV=true

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the server
python main.py