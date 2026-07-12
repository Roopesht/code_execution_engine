# Windows Setup Guide: Qwen2.5-Coder LLM

One-command setup for Windows users.

## Prerequisites

- **Windows 10/11** with WSL 2 or Hyper-V
- **Docker Desktop for Windows**
- **4GB RAM minimum**

## Installation (One Command!)

### Step 1: Install Docker Desktop

Download and install from: https://www.docker.com/products/docker-desktop

**Important Settings:**
- Enable "WSL 2 based engine" (recommended for Windows 11)
- Or use "Hyper-V" (older Windows 10)
- Allocate at least 4GB RAM in Docker Settings

### Step 2: Clone Repository

Open PowerShell and run:

```powershell
git clone <your-repo-url>
cd code_execution_engine\lms
```

### Step 3: Run One-Command Setup

**Double-click this file:**
```
quickstart.bat
```

Or run from PowerShell:
```powershell
.\quickstart.bat
```

**That's it!** The script will:
- ✅ Check Docker is installed
- ✅ Download 0.5B model (644MB)
- ✅ Start Docker container
- ✅ Test the API

**Expected time: 5-10 minutes**

---

## After Setup

### Test the API

Open PowerShell and run:

```powershell
# Health check
curl http://localhost:8001/health

# Should see: {"status":"ok"}
```

### Stop/Start Server

```powershell
cd lms\docker

# Start
docker-compose up -d llm-server

# Stop
docker-compose down

# View logs
docker logs llm-server
```

---

## Usage Examples

### PowerShell

```powershell
# Generate Python code
$response = curl -X POST http://localhost:8001/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{"model":"qwen","messages":[{"role":"user","content":"write python to find fibonacci"}],"max_tokens":200}'

$response | ConvertFrom-Json | Select-Object -ExpandProperty choices | Select-Object -First 1 | Select-Object -ExpandProperty message
```

### Python

```python
import requests

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
code = response.json()["choices"][0]["message"]["content"]
print(code)
```

### Node.js

```javascript
const fetch = require('node-fetch');

async function generateCode(prompt) {
    const response = await fetch('http://localhost:8001/v1/chat/completions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            model: 'qwen',
            messages: [{role: 'user', content: prompt}],
            max_tokens: 200,
            temperature: 0.2
        })
    });
    const data = await response.json();
    return data.choices[0].message.content;
}

generateCode('write python to find fibonacci').then(console.log);
```

---

## Troubleshooting

### Docker not starting

**Problem:** "Docker daemon is not running"

**Solution:**
1. Open Docker Desktop from Start Menu
2. Wait for it to fully load (check system tray)
3. Run `quickstart.bat` again

### Port 8001 already in use

**Problem:** "Error: Port 8001 already in use"

**Solution:**
1. Edit `lms\docker\docker-compose.yml`
2. Find: `"8001:8001"`
3. Change to: `"8002:8001"`
4. Use `http://localhost:8002` instead

Or kill the process:
```powershell
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

### Out of disk space

**Problem:** "No space left on device"

**Solution:**
```powershell
# Remove old models
rm lms\models\qwen2.5-coder-1.5b-q8_0.gguf

# Clean Docker
docker system prune -a
```

### PowerShell execution policy error

**Problem:** "cannot be loaded because running scripts is disabled"

**Solution:** Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Slow performance

1. Check Docker has enough RAM (Settings → Resources → Memory)
2. Use 0.5B model (default)
3. Close other applications
4. Check WSL 2 is enabled (Settings → General)

---

## Switch Models

After initial setup, switch to larger models:

```powershell
cd lms

# Download 1.5B (better quality, slower)
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF', 'qwen2.5-coder-1.5b-q8_0.gguf', local_dir='models')"

# Or download 3B (best quality, very slow)
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('ggml-org/Qwen2.5-Coder-3B-Q8_0-GGUF', 'qwen2.5-coder-3b-q8_0.gguf', local_dir='models')"

# Then restart
cd docker
docker-compose restart
```

Or use bash if you have Git Bash installed:
```bash
bash download_model.sh 1.5b
cd docker && docker-compose restart
```

---

## Performance Reference

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| 0.5B | 644MB | ~8s per 100 tokens | Good | Development, Testing |
| 1.5B | 1.5GB | ~12s per 100 tokens | Better | Production |
| 3.0B | 3.4GB | ~20s per 100 tokens | Best | Complex tasks |

---

## What Gets Installed

- **Docker Image:** Ubuntu 22.04 with llama.cpp
- **Model:** Qwen2.5-Coder 0.5B (512M parameters)
- **API Server:** OpenAI-compatible chat endpoint
- **Port:** 8001

---

## Need Help?

1. **Check logs:**
   ```powershell
   docker logs llm-server
   ```

2. **Test connection:**
   ```powershell
   curl http://localhost:8001/health
   ```

3. **View Docker status:**
   ```powershell
   docker-compose ps
   ```

4. **Read full documentation:** See `README.md`

---

## For Instructors

Distribute to students:
1. This file (WINDOWS_SETUP.md)
2. The `lms` folder
3. Ask them to run: `quickstart.bat`

Students should be ready in 10 minutes!

---

**Happy coding! 🚀**
