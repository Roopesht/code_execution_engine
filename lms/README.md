# Local LLM Service (Story 6.1)

OpenAI-compatible API running llama.cpp for offline code feedback.

## Quick Start

### 1. Download Model

The model is not included in the Docker image to keep build size small. Download it using the provided script:

```bash
cd lms
bash download_model.sh 1.5b

# Or download the larger 3B model for better quality:
# bash download_model.sh 3b
```

This downloads to `lms/models/` and creates `active.gguf` symlink.

### 2. Build & Start Container

```bash
cd lms/docker

# Build image
docker-compose build llm-server

# Start service
docker-compose up -d llm-server

# Wait for startup (~20 seconds)
sleep 20

# Check health
curl http://localhost:8001/health
```

### 3. Use API

```bash
# Chat completion (OpenAI compatible)
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

## Directory Structure

```
lms/
├── docker/
│   ├── Dockerfile           # Build llama.cpp
│   ├── docker-compose.yml   # Service config
│   ├── start.sh             # Startup script
│   └── .env                 # Environment variables
├── models/
│   ├── manifest.json        # Model metadata
│   ├── active.gguf          # Symlink to current model
│   ├── qwen2.5-coder-1.5b.gguf  # Downloaded model
│   └── qwen2.5-coder-3b-v2.gguf # Optional larger model
├── config/
│   └── runtime.json         # LLM runtime config
├── logs/                    # Server logs
├── cache/                   # KV cache
├── download_model.sh        # Model download script
└── README.md               # This file
```

## Model Setup

### Download Models

Using the provided script:

```bash
# Download 1.5B model (lightweight, ~1.6GB)
bash lms/download_model.sh 1.5b

# Download 3B model (better quality, ~3.4GB)
bash lms/download_model.sh 3b
```

The script:
1. Downloads the model from HuggingFace (requires internet)
2. Places it in `lms/models/`
3. Creates `active.gguf` symlink

### Manual Download

If the script fails, you can download manually:

1. Visit [Qwen2.5-Coder-GGUF on HuggingFace](https://huggingface.co/Qwen/Qwen2.5-Coder-GGUF)
2. Download `qwen2.5-coder-1.5b-q4_k_m.gguf` or `qwen2.5-coder-3b-q4_k_m.gguf`
3. Place in `lms/models/`
4. Create symlink:
   ```bash
   cd lms/models
   ln -sf qwen2.5-coder-1.5b-q4_k_m.gguf active.gguf
   ```

### Using Different Models

Edit `lms/docker/docker-compose.yml` to mount your model:

```yaml
volumes:
  - /path/to/your/model.gguf:/models/custom.gguf
  - ./llm_logs:/logs
  - ./llm_cache:/cache
```

Then update `start.sh` to point to your model, or create the symlink:

```bash
cd /models && ln -sf custom.gguf active.gguf
```

## Runtime Settings

Edit `lms/config/runtime.json`:

```json
{
  "threads": "auto",
  "context_size": 8192,
  "temperature": 0.2,
  "max_tokens": 150
}
```

- **threads**: `"auto"` (uses all CPUs) or specific number
- **context_size**: Token context window (4096-8192)
- **temperature**: 0-2.0 (higher = more creative)
- **max_tokens**: Maximum response tokens

## Health Check

```bash
curl http://localhost:8001/health | jq
```

Response:
```json
{
  "status": "healthy",
  "model": {
    "id": "qwen2.5-coder-1.5b",
    "size_mb": 1600,
    "parameterCount": 1500000000
  },
  "loaded": true,
  "uptime_seconds": 12345,
  "hardware": {
    "gpu_available": false,
    "memory_used_mb": 2048
  }
}
```

## Endpoints

### GET /health
Service health and model status

### POST /v1/chat/completions
OpenAI-compatible chat API

See [LLM_ENDPOINTS_GUIDE.md](../docs/delivery/LLM_ENDPOINTS_GUIDE.md) for complete API reference.

## Logs

```bash
# Real-time logs
docker logs -f llm-server

# Full log file
cat lms/logs/server.log
```

## Troubleshooting

### Container exits with "failed to read magic"

Model file is missing or empty. Fix:

```bash
# Download model
cd lms
bash download_model.sh 1.5b

# Restart container
cd docker
docker-compose restart llm-server
```

### "No .gguf files found"

Models directory is empty or not mounted. Check:

```bash
docker exec llm-server ls -lah /models/
```

Solution:

```bash
# Download model first
cd lms
bash download_model.sh 1.5b

# Verify file exists
ls -lah lms/models/

# Rebuild and restart
cd docker
docker-compose down
docker-compose build llm-server
docker-compose up -d llm-server
```

### Build takes too long

First build compiles llama.cpp from source (~2 minutes). Subsequent builds use cache.

To speed up llama.cpp builds:
1. Pre-built binaries can be cached
2. Adjust `-j2` flag in Dockerfile for your system

### Health check fails

Container may still be starting. Wait 60+ seconds:

```bash
docker logs llm-server  # Check startup progress
sleep 60
curl http://localhost:8001/health
```

### GPU not detected

Falls back to CPU automatically (slower but functional):

```bash
# Check GPU support (requires nvidia-docker)
docker run --rm --gpus all nvidia/cuda:11.8.0-runtime nvidia-smi
```

### Port 8001 already in use

Change port in `docker-compose.yml`:

```yaml
ports:
  - "8002:8001"  # Map 8002 on host to 8001 in container
```

Then update API calls to use port 8002.

## Models

Default: **Qwen2.5-Coder-1.5B** (lightweight, fast)

| Model | Size | Params | Context | RAM | Quality |
|-------|------|--------|---------|-----|---------|
| **Qwen 1.5B** | 1.6GB | 1.5B | 4K | 4GB | Good |
| Qwen 3B v2 | 3.4GB | 3.0B | 8K | 8GB | Better |

## Performance

**Qwen 1.5B (default):**

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Health check | < 10ms | - |
| Chat (50 tokens) | 200-400ms | ~125 tok/s |
| Chat (150 tokens) | 400-800ms | ~190 tok/s |

**Qwen 3B (if enabled):**
- 1.5-2x slower per token
- Better response quality
- ~8GB RAM required

## Integration with Executor

The executor calls `/feedback` endpoint on executor port (7998/7996/7994), which internally calls this LLM service on port 8001.

See [LLM_ENDPOINTS_GUIDE.md](../docs/delivery/LLM_ENDPOINTS_GUIDE.md) for `/feedback` endpoint specification.

## Development

### Build locally
```bash
cd lms/docker
docker-compose build llm-server
```

### Test API
```bash
# Health
curl http://localhost:8001/health

# Chat
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"test"}]}'
```

### View logs
```bash
docker logs llm-server
tail -f lms/logs/server.log
```

## Story Status

Story 6.1: Local LLM Docker Setup - ✅ Complete

See `docs/delivery/stories/6.1_local_llm_docker_setup.md` for specifications.
