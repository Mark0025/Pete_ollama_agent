# PeteOllama V1 - Python Application Container
# Uses UV for fast package management

FROM python:3.11-slim

# Install system dependencies for PyQt5 and UV
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    # Qt5 system libraries (for PyQt5)
    libqt5gui5 \
    libqt5widgets5 \
    libqt5core5a \
    qt5-qmake \
    # X11 for GUI (optional, for display)
    libx11-6 \
    libxext6 \
    # Database drivers
    libpq-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install UV (fast Python package manager) via pip
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy requirements for dependency installation
COPY pyproject.toml ./

# Install dependencies directly (skip package build)
RUN uv pip install --system \
    fastapi>=0.104.1 \
    uvicorn>=0.24.0 \
    pydantic>=2.5.0 \
    psycopg2-binary>=2.9.9 \
    requests>=2.31.0 \
    ollama>=0.1.8 \
    PyQt5>=5.15.0 \
    PyQt5-tools>=5.15.0 \
    python-dotenv>=1.0.0 \
    loguru>=0.7.2 \
    python-multipart>=0.0.6 \
    websockets>=11.0.0 \
    aiohttp>=3.9.0

# Copy application source code
COPY src/ ./src/
COPY extract_jamie_data.py ./
COPY *.py ./

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models

# Set Python path
ENV PYTHONPATH=/app

# Expose ports for FastAPI and GUI
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - webhook server only (no GUI in container)
CMD ["python", "src/webhook_only.py"]