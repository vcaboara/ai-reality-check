# Use Python 3.12 slim image
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml README.md .

# Install dependencies using uv (much faster than pip)
RUN uv pip install --system --no-cache .

# Copy application code
COPY src/ src/
COPY config/ config/

# Create data directories
RUN mkdir -p data/uploads data/results

# Expose Flask port
EXPOSE 5000

# Health check using Python (no curl needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/').read()" || exit 1

# Run server
CMD ["python", "-m", "flask", "--app", "src.ui.server:app", "run", "--host", "0.0.0.0", "--port", "5000"]
