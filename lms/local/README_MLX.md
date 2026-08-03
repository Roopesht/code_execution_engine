# MLX Local Runner for macOS

Run Qwen2.5-Coder natively on Apple Silicon Macs using MLX (no Docker needed).

## Quick Start

**Requirements:**
- Apple Silicon Mac (M1, M2, M3, etc.)
- macOS 11+
- Python 3.9+

**One command:**
```bash
bash run_local.sh
```

This will:
1. Verify your Mac is Apple Silicon
2. Create a Python virtual environment
3. Install `mlx-lm`
4. Download/cache the 0.5B model (fastest)
5. Start an OpenAI-compatible API server on port 8001

## Usage

### Default (0.5B, fastest)
```bash
bash run_local.sh
```

### Other sizes
```bash
bash run_local.sh 1.5b   # Balanced quality/speed
bash run_local.sh 3b     # Best quality
```

## API

Once running, the server is available at `http://127.0.0.1:8001`.

### List available models
```bash
curl http://127.0.0.1:8001/v1/models
```

### Chat completion (OpenAI-compatible)
```bash
curl -X POST http://127.0.0.1:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "write python fibonacci"}],
    "max_tokens": 100,
    "temperature": 0.2
  }'
```

## Managing the Server

### Stop the server
```bash
kill $(cat logs/mlx_server.pid)
```

### View server logs
```bash
tail -f logs/mlx_server.log
```

### Switch models
```bash
bash run_local.sh 1.5b
```
This automatically stops the previous server and starts the new model.

## Performance

Approximate response times on Apple Silicon:
- **0.5B** — ~1 second (base M1/M2)
- **1.5B** — 3–5 seconds (M1 Pro+, M2/M3)
- **3B** — 10–15 seconds (M3 Max, requires 8GB+ RAM)

## Comparison to Docker

| Aspect | MLX Local | Docker (llama.cpp) |
|--------|-----------|---|
| Setup time | ~5 min (first run, model download) | ~10 min (build + download) |
| Inference speed | ⚡ Optimized for Apple Silicon | ⚠️ CPU fallback, slower |
| Memory | Efficient (quantized 4-bit) | Higher overhead (container) |
| No. of steps | 1 command | 2–3 commands |
| Drop-in replacement | ✓ (same port 8001, same API) | — |

## Troubleshooting

**Platform not supported:**
```
✗ Apple Silicon required
  MLX requires Apple Silicon (arm64 CPU)
```
→ MLX only runs on Apple Silicon Macs. For Intel Macs, use Docker via `bash quickstart.sh`.

**Port 8001 already in use:**
```
✗ Port 8001 is already in use
  If running via Docker, stop it with: cd lms/docker && docker-compose down
```
→ Stop any competing process and re-run.

**Model download fails:**
→ Check your internet connection, then try again. The script will resume from the cache.

**Python version too old:**
```
✗ Python 3.9+ required (found: 3.8)
```
→ Install Python 3.9 or newer from [python.org](https://www.python.org/downloads/).

## Under the Hood

- **Virtual environment** — `mlx_env/` (auto-created, auto-activated)
- **Model cache** — `~/.cache/huggingface/` (shared across projects)
- **Logs** — `logs/mlx_server.log`
- **PID file** — `logs/mlx_server.pid` (for clean shutdown)

The script uses `mlx_lm.server`, which exposes the same OpenAI-compatible endpoints as the Docker setup (`/v1/chat/completions`, `/v1/models`) — no code changes needed if you're already using the Docker API.
