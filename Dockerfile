FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY config/ config/
COPY data/ data/

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install --system -e .

# Expose port
EXPOSE 5000

# Run server
CMD ["python", "src/ui/server.py"]
