#!/bin/bash

# Quickstart: Install & run Qwen2.5-Coder LLM with Docker
# One-step setup for students
# Usage: bash quickstart.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Qwen2.5-Coder LLM - Quick Setup                       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "✓ Checking requirements..."

if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ docker-compose not found"
    exit 1
fi

echo "✓ Docker installed"
echo ""

# Download model
echo "Downloading Qwen2.5-Coder 0.5B model (644MB)..."
bash download_model.sh 0.5b
echo ""

# Start Docker
echo "Starting Docker container..."
cd docker
docker-compose down 2>/dev/null || true
docker-compose up -d llm-server
echo ""

# Wait for server
echo "Waiting for server to start (30 seconds)..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✓ Server is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup Complete!                                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 API is running at: http://localhost:8001"
echo ""
echo "📝 Quick Test:"
echo ""
echo "   # Health check"
echo "   curl http://localhost:8001/health"
echo ""
echo "   # Chat with the model"
echo "   curl -X POST http://localhost:8001/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\":\"qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"write python to find fibonacci\"}],\"max_tokens\":100}'"
echo ""
echo "📚 Full documentation: See README.md and MODEL_SIZES.md"
echo ""
echo "🔄 To switch models:"
echo "   bash download_model.sh 1.5b  # or 3b"
echo "   cd docker && docker-compose restart"
echo ""
