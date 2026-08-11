# Setup Local Code Execution Engine

**Requires:** Docker (must be installed)

---

## 🚀 Express Setup (Beginners)

**Time:** 5 minutes | **Complexity:** Minimal

### Step 1: Clone Repository

```bash
git clone <repo>
cd code_execution_engine
```

### Step 2: Create Configuration

**Mac/Linux:**
```bash
cp .env.example .env
```

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

### Step 3: Set API Key

Edit `.env` file:

```bash
EXECUTOR_API_KEY=test_key_12345678901234567890
```

(Any string with 32+ characters works for learning)

### Step 4: Run with docker-compose (Easiest)

```bash
docker-compose up --build -d
```

### Done ✅

**HTTPS** running at: `https://localhost:7998`

Verify (ignore self-signed cert warning):
```bash
curl -k https://localhost:7998/health
```

Or open browser: https://localhost:7998/docs (click "Advanced" → "Accept Risk")

### About Certificates

This setup uses **self-signed SSL certificates** for local development:
- **Public cert:** `./certs/server-cert.pem` ✅ (safe to share with team)
- **Private key:** `./certs/server-key.pem` ❌ (NEVER share or commit)

The certificate is already included - just works out of the box!

---

## 🔧 Advanced Setup (For experienced people)

**Time:** 15 minutes | **Complexity:** Detailed configuration

### Step 1: Clone Repository

```bash
git clone <repo>
cd code_execution_engine
```

### Step 2: Configure Environment

**Mac/Linux:**
```bash
cp .env.example .env
nano .env
```

**Windows (Command Prompt):**
```cmd
copy .env.example .env
notepad .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```

### Step 3: Generate Strong API Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy output and set in `.env`:
```bash
EXECUTOR_API_KEY=<your_generated_key>
```

### Step 4: Set CORS Origins

Edit `.env` with your domain(s):
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Step 5: Configure Resources (Optional)

Edit `.env`:
```bash
EXECUTION_TIMEOUT=5              # Seconds
CONTAINER_MEMORY_MB=512          # MB
CONTAINER_CPU_LIMIT=0.5          # CPU cores
LOG_LEVEL=INFO                   # INFO or DEBUG
```

### Step 6: Build & Run with Auto-Restart

```bash
docker build -t code-executor .

docker run -d \
  -p 7998:7998 \
  --env-file .env \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --restart=unless-stopped \
  --name code-executor \
  code-executor
```

### Step 7: Verify

```bash
# Running?
docker ps | grep code-executor

# Health check
curl http://localhost:7998/health

# Test execution
curl -X POST http://localhost:7998/execute \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "exerciseId": "test",
    "code": "def add(a, b):\n  return a + b",
    "tests": "def test():\n  assert add(1, 1) == 2"
  }'
```

Expected: `"passed": true`

### Production Checklist

- [ ] Strong API key (64+ characters)
- [ ] CORS_ORIGINS = your domain
- [ ] LOG_LEVEL = INFO
- [ ] Resource limits set
- [ ] Auto-restart enabled
- [ ] Monitoring configured
- [ ] API key rotated every 90 days

---

## Troubleshooting

### Docker not installed
```
Error: docker: command not found
```
**Solution:** Install Docker Desktop or Docker Engine

### Port 7998 in use
```
Error: Address already in use
```
**Solution:** 
```bash
docker-compose down
docker-compose up --build
```

### Health check fails
```
curl: (7) Failed to connect
```
**Solution:** Check logs
```bash
docker logs code-executor
```

### Docker socket permission denied
```
Error: /var/run/docker.sock: Permission denied
```
**Solution:** 
```bash
sudo usermod -aG docker $USER
# Then logout and login again
```

---

## Next Steps

1. ✅ Engine is running
2. 📖 Read [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) to integrate with your website
3. 🔒 See [docs/delivery/SECURITY_CONFIGURATION.md](docs/delivery/SECURITY_CONFIGURATION.md) for security

---


docker compose down
docker compose up -d --build

docker compose logs -f