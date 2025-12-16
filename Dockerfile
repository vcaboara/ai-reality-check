# Use Python 3.12 slim image
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml .

# Install dependencies using uv (much faster than pip)
RUN uv pip install --system --no-cache .

# Copy application code
COPY src/ src/
COPY config/ config/

# Create data directories
RUN mkdir -p data/uploads data/results

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run server
CMD ["python", "-m", "flask", "--app", "src.ui.server:app", "run", "--host", "0.0.0.0", "--port", "5000"]
