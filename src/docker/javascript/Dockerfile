# JavaScript/Node.js Execution Environment
FROM node:20-slim

WORKDIR /workspace

# Install testing frameworks globally
RUN npm install -g --silent \
    jest@29.7.0 \
    mocha@10.2.0 \
    chai@4.3.10

# Create non-root user for execution
RUN useradd -m -u 1000 executor
USER executor

# Default command
CMD ["/bin/bash"]
