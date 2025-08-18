# PeteOllama V1 - Production Dockerfile
# Lightweight deployment with RunPod serverless backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.lightweight.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.lightweight.txt

# Copy source code
COPY src/ ./src/
COPY langchain_indexed_conversations.json ./
COPY .env* ./

# Create necessary directories
RUN mkdir -p logs data

# Set Python path
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["python", "src/main.py"]

# Jamie (PeteOllama V2) - Production Docker Image
# Simple single-stage build

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash jamie

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=jamie:jamie . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models && \
    chown -R jamie:jamie /app

# Set environment variables
ENV PYTHONPATH=/app \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Switch to non-root user
USER jamie

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "src/main.py"]
