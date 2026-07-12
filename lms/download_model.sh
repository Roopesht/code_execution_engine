#!/bin/bash

# Download Qwen2.5-Coder model for local LLM service
# Tries multiple sources: official Qwen GGUF repos, community GGUF quantizations, or Ollama
# Usage: bash download_model.sh [1.5b|3b]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/models"
MODEL_SIZE="${1:-1.5b}"

mkdir -p "$MODELS_DIR"

case "$MODEL_SIZE" in
  1.5b)
    MODEL_NAME="qwen2.5-coder-1.5b"
    FILENAME="qwen2.5-coder-1.5b-q8_0.gguf"
    # Official GGUF quantizations from ggml-org
    REPOS=(
      "ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF"
      "ggml-org/Qwen2.5-Coder-1.5B-Q6_K-GGUF"
      "ggml-org/Qwen2.5-Coder-1.5B-Q5_K_M-GGUF"
      "ggml-org/Qwen2.5-Coder-1.5B-Q4_K_M-GGUF"
    )
    OLLAMA_MODEL="qwen2.5-coder:1.5b"
    ;;
  3b)
    MODEL_NAME="qwen2.5-coder-3b"
    FILENAME="qwen2.5-coder-3b-q8_0.gguf"
    REPOS=(
      "ggml-org/Qwen2.5-Coder-3B-Q8_0-GGUF"
      "ggml-org/Qwen2.5-Coder-3B-Q6_K-GGUF"
      "ggml-org/Qwen2.5-Coder-3B-Q5_K_M-GGUF"
      "ggml-org/Qwen2.5-Coder-3B-Q4_K_M-GGUF"
    )
    OLLAMA_MODEL="qwen2.5-coder:3b"
    ;;
  *)
    echo "Usage: $0 [1.5b|3b]"
    echo "  1.5b - Lightweight model (~1.6GB, requires 4GB RAM)"
    echo "  3b  - Better quality model (~3.4GB, requires 8GB RAM)"
    exit 1
    ;;
esac

OUTPUT_FILE="$MODELS_DIR/$FILENAME"

# Check if model already exists
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    SIZE=$(du -sh "$OUTPUT_FILE" | cut -f1)
    echo "✓ Model already exists: $OUTPUT_FILE ($SIZE)"
    cd "$MODELS_DIR"
    ln -sf "$FILENAME" active.gguf 2>/dev/null || true
    echo "✓ Symlink ready: active.gguf"
    exit 0
fi

echo "Downloading Qwen2.5-Coder-$MODEL_SIZE model..."
echo "File: $FILENAME"
echo "Destination: $MODELS_DIR/"
echo ""

# Try Ollama first if available (simplest method)
if command -v ollama &> /dev/null; then
    echo "✓ Ollama detected. Downloading via Ollama..."
    ollama pull "$OLLAMA_MODEL" && {
        # Try to export from Ollama cache
        echo "Note: Model downloaded to Ollama. You can run directly with:"
        echo "  ollama run $OLLAMA_MODEL"
        # Don't exit - continue to try HF as well
    }
fi

# Try HF repos in order
SUCCESS=0
for REPO_ID in "${REPOS[@]}"; do
    echo "Trying: $REPO_ID"

    if command -v hf &> /dev/null; then
        hf download "$REPO_ID" "$FILENAME" --local-dir "$MODELS_DIR" 2>/dev/null && SUCCESS=1 && break
    elif command -v huggingface-cli &> /dev/null; then
        huggingface-cli download "$REPO_ID" "$FILENAME" --local-dir "$MODELS_DIR" 2>/dev/null && SUCCESS=1 && break
    fi
done

# If no HF tool exists, try to install
if [ $SUCCESS -eq 0 ] && ! command -v hf &> /dev/null && ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface-hub..."
    pip3 install -q huggingface-hub 2>&1 || pip install -q huggingface-hub 2>&1 || true

    # Retry with each repo
    for REPO_ID in "${REPOS[@]}"; do
        echo "Trying: $REPO_ID"

        if command -v hf &> /dev/null; then
            hf download "$REPO_ID" "$FILENAME" --local-dir "$MODELS_DIR" 2>/dev/null && SUCCESS=1 && break
        elif command -v huggingface-cli &> /dev/null; then
            huggingface-cli download "$REPO_ID" "$FILENAME" --local-dir "$MODELS_DIR" 2>/dev/null && SUCCESS=1 && break
        fi
    done
fi

if [ $SUCCESS -eq 1 ]; then
    # Create symlink
    cd "$MODELS_DIR"
    ln -sf "$FILENAME" active.gguf

    SIZE=$(du -sh "$FILENAME" | cut -f1)
    echo ""
    echo "✓ Download complete!"
    echo "  File: $FILENAME"
    echo "  Size: $SIZE"
    echo "✓ Symlink created: active.gguf"
    echo ""
    echo "Ready to start! Run:"
    echo "  cd lms/docker && docker-compose up -d llm-server"
else
    echo ""
    echo "✗ All automated download methods failed"
    echo ""
    echo "Options:"
    echo ""
    echo "1. Manual download from HuggingFace:"
    echo "   - Visit: https://huggingface.co/Qwen"
    echo "   - Search for 'Coder' GGUF quantizations"
    echo "   - Download: $FILENAME (~1.6-3.4 GB)"
    echo "   - Save to: $MODELS_DIR/"
    echo "   - Create symlink: cd $MODELS_DIR && ln -sf $FILENAME active.gguf"
    echo ""
    echo "2. Try community GGUF repos:"
    echo "   - bartowski GGUF: https://huggingface.co/bartowski"
    echo "   - TheBloke GGUF: https://huggingface.co/TheBloke"
    echo "   - QuantFactory: https://huggingface.co/QuantFactory"
    echo ""
    echo "3. Use Ollama (if installed):"
    echo "   - ollama pull $OLLAMA_MODEL"
    exit 1
fi
