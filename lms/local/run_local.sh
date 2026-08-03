#!/bin/bash

# Native macOS MLX runner for Qwen2.5-Coder
# One-step setup: install MLX, download model, run OpenAI-compatible API server on port 8001
# Usage: bash run_local.sh [0.5b|1.5b|3b]
# Requires: Apple Silicon Mac (arm64), Python 3.9+

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Qwen2.5-Coder LLM - MLX Local Setup (macOS)           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Platform guard: MLX requires Apple Silicon
if [ "$(uname -s)" != "Darwin" ]; then
    echo "✗ macOS required"
    echo "   MLX only runs on macOS (currently detected: $(uname -s))"
    exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
    echo "✗ Apple Silicon required"
    echo "   MLX requires Apple Silicon (arm64 CPU)"
    echo "   Your Mac is: $(uname -m)"
    exit 1
fi

echo "✓ Platform: macOS Apple Silicon"
echo ""

# Parse model size argument
MODEL_SIZE="${1:-0.5b}"
case "$MODEL_SIZE" in
  0.5b)
    MODEL_REPO="mlx-community/Qwen2.5-Coder-0.5B-Instruct-4bit"
    echo "Selected: 0.5B model (fastest, ~400MB, 512M params)"
    ;;
  1.5b)
    MODEL_REPO="mlx-community/Qwen2.5-Coder-1.5B-Instruct-4bit"
    echo "Selected: 1.5B model (balanced, ~1.5GB, 1.5B params)"
    ;;
  3b|3.0b)
    MODEL_REPO="mlx-community/Qwen2.5-Coder-3B-Instruct-4bit"
    echo "Selected: 3.0B model (best quality, ~3.4GB, 3.0B params)"
    ;;
  *)
    echo "Usage: $0 [0.5b|1.5b|3b]"
    echo ""
    echo "Model sizes:"
    echo "  0.5b - Ultra-fast (~400MB, 512M params, ~1 sec per response)"
    echo "  1.5b - Balanced (~1.5GB, 1.5B params, ~3-5 sec per response)"
    echo "  3b  - Best quality (~3.4GB, 3.0B params, ~10-15 sec per response)"
    exit 1
    ;;
esac
echo ""

# Setup logs directory (needed early for PID file check)
mkdir -p logs

# Stop any existing server before checking port availability
if [ -f "logs/mlx_server.pid" ]; then
    OLD_PID=$(cat logs/mlx_server.pid 2>/dev/null)
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping previous MLX server (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
fi

# Check port 8001 is available (after killing old server)
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✗ Port 8001 is still in use (not from MLX)"
    echo ""
    echo "If running via Docker, stop it with:"
    echo "  cd lms/docker && docker-compose down"
    echo ""
    exit 1
fi

# Check Python 3.9+
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found"
    echo "   Install from: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MIN="3.9"
if [ "$(printf '%s\n' "$PYTHON_MIN" "$PYTHON_VERSION" | sort -V | head -n1)" != "$PYTHON_MIN" ]; then
    echo "✗ Python 3.9+ required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION installed"
echo ""

# Create/setup venv
VENV_DIR="mlx_env"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" >/dev/null 2>&1
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing mlx-lm..."
pip install -q -U pip >/dev/null 2>&1
pip install -q mlx-lm >/dev/null 2>&1

echo "✓ MLX setup complete"
echo ""

# Download/cache model
echo "Preparing model (downloading/caching if needed)..."
python3 << PYTHON_EOF
from mlx_lm import load

try:
    print("  Loading model weights from HuggingFace...", end=" ", flush=True)
    model, tokenizer = load("$MODEL_REPO")
    print("✓")
except Exception as e:
    print(f"\n✗ Failed to load model: {e}", file=sys.stderr)
    exit(1)
PYTHON_EOF

echo ""

# Start MLX server
echo "Starting MLX server on port 8001..."
nohup python3 -m mlx_lm.server \
    --model "$MODEL_REPO" \
    --host 127.0.0.1 \
    --port 8001 \
    --max-tokens 150 \
    --temp 0.2 \
    > logs/mlx_server.log 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" > logs/mlx_server.pid
echo ""

# Wait for server readiness
echo "Waiting for server to start (up to 60 seconds)..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:8001/v1/models >/dev/null 2>&1; then
        echo "✓ Server is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ MLX Server Started!                                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 API is running at: http://127.0.0.1:8001"
echo ""
echo "📝 Quick Test:"
echo ""
echo "   # List models"
echo "   curl http://127.0.0.1:8001/v1/models"
echo ""
echo "   # Chat with the model"
echo "   curl -X POST http://127.0.0.1:8001/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\":\"qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"write python to find fibonacci\"}],\"max_tokens\":100}'"
echo ""
echo "📚 Full documentation: See README.md and MODEL_SIZES.md"
echo ""
echo "🔄 To switch models:"
echo "   bash run_local.sh 1.5b  # or 3b"
echo ""
echo "🛑 To stop the server:"
echo "   kill $(cat logs/mlx_server.pid) 2>/dev/null || true"
echo ""
