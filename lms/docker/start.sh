#!/bin/bash

set -e

echo "[$(date)] LLM Server Starting..."

# Load environment variables
CONFIG_PATH="${CONFIG_PATH:-/app/runtime.json}"
MODELS_PATH="${MODELS_PATH:-/models}"
LOG_PATH="${LOG_PATH:-/logs}"
MODEL_PATH="${MODEL_PATH:-/models/active.gguf}"

# Verify models directory exists
if [ ! -d "$MODELS_PATH" ]; then
    echo "[ERROR] Models directory not found: $MODELS_PATH"
    exit 1
fi

# Create symlink if it doesn't exist
if [ ! -L "$MODEL_PATH" ]; then
    # Find first available .gguf file
    FIRST_MODEL=$(ls "$MODELS_PATH"/*.gguf 2>/dev/null | head -1)
    if [ -n "$FIRST_MODEL" ]; then
        ln -sf "$(basename $FIRST_MODEL)" "$MODELS_PATH/active.gguf"
        echo "[$(date)] Created symlink: active.gguf -> $(basename $FIRST_MODEL)"
    fi
fi

# Verify active.gguf exists and is valid
if [ ! -f "$MODEL_PATH" ] && [ ! -L "$MODEL_PATH" ]; then
    echo "[ERROR] Active model not found: $MODEL_PATH"
    echo "[ERROR] Available models in $MODELS_PATH:"
    ls -lah "$MODELS_PATH"/*.gguf 2>/dev/null || echo "  No .gguf files found"
    echo ""
    echo "[ERROR] To fix this:"
    echo "  1. Download a model: curl -L -o qwen2.5-coder-1.5b.gguf <huggingface-url>"
    echo "  2. Place in: $MODELS_PATH/"
    echo "  3. Restart container: docker-compose restart"
    exit 1
fi

# Resolve symlink to actual file
ACTUAL_MODEL=$(readlink -f "$MODEL_PATH")
if [ ! -f "$ACTUAL_MODEL" ]; then
    echo "[ERROR] Model file not found: $ACTUAL_MODEL"
    exit 1
fi

# Log model info
MODEL_NAME=$(basename "$ACTUAL_MODEL")
MODEL_SIZE=$(du -sh "$ACTUAL_MODEL" | cut -f1)
echo "[$(date)] Model: $MODEL_NAME ($MODEL_SIZE)"
echo "[$(date)] Config: $CONFIG_PATH"

# Verify config exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "[ERROR] Config not found: $CONFIG_PATH"
    exit 1
fi

# Create logs directory
mkdir -p "$LOG_PATH"

# Parse configuration
THREADS=$(grep -o '"threads": "[^"]*"' "$CONFIG_PATH" | cut -d'"' -f4)
CONTEXT=$(grep -o '"context_size": [^,}]*' "$CONFIG_PATH" | cut -d':' -f2 | tr -d ' ')
TEMPERATURE=$(grep -o '"temperature": [^,}]*' "$CONFIG_PATH" | cut -d':' -f2 | tr -d ' ')
MAX_TOKENS=$(grep -o '"max_tokens": [^,}]*' "$CONFIG_PATH" | cut -d':' -f2 | tr -d ' ')

# Resolve "auto" threads to actual CPU count
if [ "$THREADS" = "auto" ]; then
  THREADS=$(nproc)
fi

echo "[$(date)] Configuration:"
echo "[$(date)]   Threads: $THREADS"
echo "[$(date)]   Context: $CONTEXT"
echo "[$(date)]   Temperature: $TEMPERATURE"
echo "[$(date)]   Max Tokens: $MAX_TOKENS"

# Start llama.cpp server
echo "[$(date)] Starting llama-server..."
echo "[$(date)] Listening on http://0.0.0.0:8001"

cd /app/llama.cpp/build/bin

./llama-server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port 8001 \
    --threads $THREADS \
    --ctx-size $CONTEXT \
    --parallel 2 \
    --cache-type-k q8_0 \
    --cache-type-v q8_0 \
    2>&1 | tee "$LOG_PATH/server.log"
