# Code Execution Engine API Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY run_dual.py .

# Expose ports (HTTP and HTTPS)
EXPOSE 7999 7998

# Run both HTTP and HTTPS servers
CMD ["python", "run_dual.py"]
