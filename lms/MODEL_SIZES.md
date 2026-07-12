# Qwen2.5-Coder Model Sizes

Quick reference for switching between model sizes.

## Available Models

| Size | Params | File Size | Speed | Quality | Best For |
|------|--------|-----------|-------|---------|----------|
| **0.5B** | 512M | ~400MB | ⚡⚡⚡ Very Fast (1-2 sec) | Good | M1 Mac, Mobile, Real-time |
| **1.5B** | 1.5B | ~1.5GB | ⚡⚡ Fast (3-5 sec) | Better | Balanced, Development |
| **3.0B** | 3.0B | ~3.4GB | ⚡ Slower (10-15 sec) | Best | Production, Complex code |

## Download & Switch

```bash
# Download 0.5B (fastest for M1 Mac)
bash lms/download_model.sh 0.5b

# Download 1.5B (balanced)
bash lms/download_model.sh 1.5b

# Download 3.0B (best quality)
bash lms/download_model.sh 3b

# Restart Docker after downloading
cd lms/docker && docker-compose restart
```

## Model Paths

Each model is stored in `lms/models/` with an `active.gguf` symlink pointing to the current model:

```
lms/models/
├── qwen2.5-coder-0.5b-q8_0.gguf    → Latest 0.5B download
├── qwen2.5-coder-1.5b-q8_0.gguf    → Latest 1.5B download
├── qwen2.5-coder-3b-q8_0.gguf      → Latest 3.0B download
└── active.gguf                      → Symlink to active model
```

## Runtime Settings

Edit `lms/config/runtime.json` for performance tuning:

```json
{
  "threads": "auto",           # Auto-detect CPU threads
  "context_size": 8192,        # Token context window
  "temperature": 0.2,          # 0=deterministic, 1=creative
  "max_tokens": 150            # Max response length
}
```

For faster responses on M1 Mac with 0.5B:
- Reduce `max_tokens` to 50-100
- Increase `temperature` to 0.5-0.7 for more varied responses

## Performance Tips

### M1 Mac (Docker - CPU only)
- **Recommended**: 0.5B model (fastest)
- 1.5B model is acceptable but slow (12+ sec)
- 3B model is too slow for interactive use

### To Speed Up Further
1. Reduce `context_size` from 8192 to 4096
2. Reduce `max_tokens` from 150 to 50-100
3. Use Ollama (native Metal GPU): `ollama run qwen2.5-coder:0.5b`
4. Run llama.cpp natively (not Docker)

## Memory Requirements

- **0.5B**: 1GB RAM minimum
- **1.5B**: 4GB RAM minimum  
- **3.0B**: 8GB RAM minimum

## Quantization Levels

Available quantizations (larger = better quality, slower):

- **Q4_K_M** - Smallest, fastest (~30% smaller than Q8_0)
- **Q5_K_M** - Balanced (~60% of Q8_0 size)
- **Q6_K** - Good quality (~70% of Q8_0 size)
- **Q8_0** - Highest quality (full precision), largest file

To use different quantization:
```bash
# Edit download_model.sh REPOS array or manually download from HuggingFace
```

## Examples

### Fast responses (0.5B, max 50 tokens)
```bash
bash lms/download_model.sh 0.5b
# Edit lms/config/runtime.json: "max_tokens": 50
cd lms/docker && docker-compose restart
```

### Balanced (1.5B, max 150 tokens)
```bash
bash lms/download_model.sh 1.5b
cd lms/docker && docker-compose restart
```

### Best quality (3.0B, max 200 tokens)
```bash
bash lms/download_model.sh 3b
cd lms/docker && docker-compose restart
```
