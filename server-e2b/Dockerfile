# E2B Dockerfile for AI Code Automation API
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install global npm packages for AI agents
RUN npm install -g @anthropic-ai/sdk

# Create app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /tmp/ai-workspace /app/logs

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app /tmp/ai-workspace

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ping || exit 1

# Switch to non-root user
USER appuser

# Set environment variables
ENV FLASK_ENV=production \
    E2B_ENV=true \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Run the Flask app directly
CMD ["python", "main.py"]