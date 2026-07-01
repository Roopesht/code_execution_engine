# Python Execution Environment
FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies and testing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python testing frameworks
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-cov==4.1.0 \
    pytest-timeout==2.2.0

# Create non-root user for execution
RUN useradd -m -u 1000 executor
USER executor

# Default command
CMD ["/bin/bash"]
