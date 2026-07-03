# Code Execution Engine API Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Docker CLI (lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY run.py .

# Expose port
EXPOSE 7999

# Run as root to access Docker socket
USER root

# Run application
CMD ["python", "run.py"]
