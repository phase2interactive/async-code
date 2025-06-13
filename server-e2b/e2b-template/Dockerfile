# Custom E2B template for async-code agents
# This template pre-installs all required dependencies to speed up task execution

FROM e2b/default:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3 \
    python3-pip \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    openai \
    anthropic \
    requests

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-cli

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Verify installations
RUN echo "=== Installed versions ===" && \
    echo "Node.js: $(node --version)" && \
    echo "npm: $(npm --version)" && \
    echo "Python: $(python3 --version)" && \
    echo "pip: $(pip3 --version)" && \
    echo "git: $(git --version)" && \
    echo "Claude CLI: $(claude --version 2>/dev/null || echo 'Not installed correctly')"

# Set environment
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production