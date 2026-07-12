# Student Setup Guide: Qwen2.5-Coder LLM

One-command setup for running a local AI model that generates Python code.

## Prerequisites

- **Docker Desktop** (Mac/Windows) or **Docker** (Linux)
- **Git** (to clone the repository)
- **4GB RAM minimum**

## Quick Start (Choose Your Platform)

### 🪟 Windows Users
```bash
# Just double-click this file:
quickstart.bat

# Or from PowerShell:
.\quickstart.bat
```
See: [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

### 🐧 Mac & Linux Users
```bash
bash quickstart.sh
```

---

## Manual Installation

### 1️⃣ Install Docker

#### Mac (Intel/Apple Silicon)
```bash
# Download & install Docker Desktop
https://www.docker.com/products/docker-desktop
```

#### Windows
```bash
# Download & install Docker Desktop
https://www.docker.com/products/docker-desktop
```

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2️⃣ Clone Repository
```bash
git clone <repo-url>
cd code_execution_engine/lms
```

### 3️⃣ Run One-Command Setup

```bash
bash quickstart.sh
```

That's it! The script will:
- ✅ Check Docker is installed
- ✅ Download the 0.5B model (644MB)
- ✅ Build the Docker image
- ✅ Start the API server
- ✅ Test the connection

**Expected time: 5-10 minutes** (mostly downloading the model)

## Verification

After setup completes, verify it's working:

```bash
# Health check
curl http://localhost:8001/health

# Should return:
# {"status": "ok"}
```

## Usage

### Python Code Generation

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "user", "content": "write python to find fibonacci numbers"}
    ],
    "max_tokens": 200,
    "temperature": 0.2
  }'
```

### Using in Python

```python
import requests
import json

url = "http://localhost:8001/v1/chat/completions"
payload = {
    "model": "qwen",
    "messages": [
        {"role": "user", "content": "write python to sort a list"}
    ],
    "max_tokens": 200,
    "temperature": 0.2
}

response = requests.post(url, json=payload)
result = response.json()
code = result['choices'][0]['message']['content']
print(code)
```

## Commands

### Start the Server
```bash
cd lms/docker
docker-compose up -d llm-server
```

### Stop the Server
```bash
cd lms/docker
docker-compose down
```

### View Logs
```bash
docker logs llm-server
```

### Switch Models

```bash
# 0.5B (fastest, currently running)
bash lms/download_model.sh 0.5b

# 1.5B (better quality, slower)
bash lms/download_model.sh 1.5b

# 3.0B (best quality, very slow)
bash lms/download_model.sh 3b

# Restart after switching
cd lms/docker && docker-compose restart
```

## Performance

On typical hardware:
- **0.5B model**: ~8 seconds per 100 tokens
- **1.5B model**: ~12 seconds per 100 tokens
- **3.0B model**: ~20+ seconds per 100 tokens

## Troubleshooting

### Docker not found
```bash
# Check if Docker is installed
docker --version

# If not installed, download Docker Desktop from:
https://www.docker.com/products/docker-desktop
```

### Port 8001 already in use
```bash
# Edit lms/docker/docker-compose.yml
# Change:   "8001:8001"
# To:       "8002:8001"
# Then use: http://localhost:8002
```

### Out of disk space
The models take up space. Clean up:
```bash
# Remove old models
rm lms/models/qwen2.5-coder-1.5b-q8_0.gguf

# Clear Docker cache
docker system prune -a
```

### Slow performance
1. Use 0.5B model (default)
2. Reduce `max_tokens` in your request
3. Close other applications
4. Check Docker has enough memory (Settings → Resources)

## For Instructors

To automate student setup:

```bash
# One-liner to setup all students' machines
bash quickstart.sh
```

Or in a shell script:
```bash
#!/bin/bash
git clone <repo-url>
cd code_execution_engine/lms
bash quickstart.sh
```

## What's Running

- **Model**: Qwen2.5-Coder 0.5B (512M parameters)
- **Framework**: llama.cpp (C++ inference engine)
- **API**: OpenAI-compatible chat completions
- **Port**: 8001
- **Container**: Docker (Linux-based)

## API Reference

See [README.md](README.md) for full API documentation.

Quick endpoints:
- `GET /health` - Server status
- `POST /v1/chat/completions` - Generate code

## Need Help?

1. Check logs: `docker logs llm-server`
2. Verify health: `curl http://localhost:8001/health`
3. Read README.md for detailed documentation
4. Check MODEL_SIZES.md for performance tuning

## Next Steps

1. ✅ Setup complete
2. Test with: `curl http://localhost:8001/health`
3. Write your first request (see "Usage" section)
4. Integrate into your Python/Node.js application
5. Switch models as needed (see "Switch Models" section)

---

**Happy coding! 🚀**
