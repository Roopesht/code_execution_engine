# Local LLM Service with llama.cpp + Default Model
# Runs OpenAI-compatible API for offline code feedback
# Includes Qwen2.5-Coder-3B by default

FROM ubuntu:22.04

WORKDIR /app

# Install build and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Clone and build llama.cpp using CMake
# Use -j2 to limit parallel builds and avoid running out of memory
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j2

# Create placeholder for model (mount actual model via docker-compose)
# Model should be provided at runtime to avoid large build context
RUN mkdir -p /models && \
    echo "Qwen2.5-Coder-1.5B model should be mounted at /models" && \
    echo "See docker-compose.yml and README.md for setup instructions"

# Create symlink to active model
RUN cd /models && \
    ln -sf qwen2.5-coder-1.5b.gguf active.gguf && \
    echo "[$(date)] Active model symlink created"

# Optional: Download larger 3B model for better quality (uncomment if needed)
# RUN cd /models && \
#    echo "[$(date)] Downloading Qwen2.5-Coder-3B model..." && \
#    wget -q --show-progress \
#      "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-GGUF/resolve/main/qwen2.5-coder-3b-q4_k_m.gguf" \
#      -O "qwen2.5-coder-3b-v2.gguf"

# Copy manifest with model metadata
COPY lms/models/manifest.json /models/manifest.json

# Copy startup script
COPY lms/docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Copy runtime config
COPY lms/config/runtime.json /app/runtime.json

# Create directories for volumes
RUN mkdir -p /cache /logs && \
    chmod -R 777 /cache /logs

# Expose API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Set environment variables
ENV MODEL_PATH=/models/active.gguf
ENV CONFIG_PATH=/app/runtime.json
ENV CACHE_PATH=/cache
ENV LOG_PATH=/logs
ENV PATH="/app/llama.cpp:${PATH}"

# Verify model on startup
RUN ls -lh /models/active.gguf

# Run startup script
CMD ["/app/start.sh"]
