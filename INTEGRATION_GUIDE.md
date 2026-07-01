# Integration Guide - Local Code Execution Engine

**For:** Web apps, learning platforms, IDEs needing safe code execution

---

## What You Get

- **Safe code execution** in isolated Docker containers
- **Multi-language support** (Python, JavaScript - more coming)
- **Automatic test execution** with detailed results
- **Novice-friendly error messages** with hints
- **API-first design** for easy integration

---

## Deployment

### Option 1: Docker (Recommended)

```bash
# Clone
git clone <repo>
cd code_execution_engine

# Setup
cp .env.example .env
# Edit .env: change EXECUTOR_API_KEY, CORS_ORIGINS

# Run
docker build -t code-executor .
docker run -d \
  -p 7999:7999 \
  --env-file .env \
  -v /var/run/docker.sock:/var/run/docker.sock \
  code-executor
```

**Important:** Container needs Docker socket to spawn execution containers.

### Option 2: Local Python

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
EXECUTOR_API_KEY=your_key_here python run.py
```

---

## API Reference

### Health Check

```
GET /health
```
No auth required. Returns `{"status": "running"}`.

### Execute Code

```
POST /execute
X-API-Key: your_api_key
Content-Type: application/json

{
  "language": "python",              // or "javascript"
  "exerciseId": "exercise_slug",     // alphanumeric + underscore
  "code": "def add(a, b):\n  return a + b",
  "tests": "def test_add():\n  assert add(1, 2) == 3",
  "timeout": 5                       // optional, 1-30 seconds
}
```

**Response (Success):**
```json
{
  "passed": true,
  "totalTests": 2,
  "passedTests": 2,
  "failedTests": 0,
  "executionTime": 0.234,
  "memory": 12.5,
  "stdout": "=== test session starts ===\n...",
  "stderr": "",
  "tests": [
    {
      "name": "test_add",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    },
    {
      "name": "test_multiply",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    }
  ],
  "error": null
}
```

**Response (With Failures - Human-Readable Error Details):**
```json
{
  "passed": false,
  "totalTests": 2,
  "passedTests": 1,
  "failedTests": 1,
  "executionTime": 0.456,
  "memory": 12.5,
  "stdout": "=== test session starts ===\n...",
  "stderr": "",
  "tests": [
    {
      "name": "test_add",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    },
    {
      "name": "test_divide",
      "status": "Failed",
      "expected": "Infinity",
      "actual": "ZeroDivisionError",
      "error": "assert <result> == Infinity",
      "stackTrace": "where ZeroDivisionError = divide(10, 0)"
    }
  ],
  "error": null
}
```

**Note:** For failed tests, each test result includes:
- `expected` - What the test expected
- `actual` - What the code returned/error type
- `error` - The assertion that failed (human-readable)
- `stackTrace` - Additional context (e.g., which function caused the issue)

These details help novice users understand exactly what went wrong and how to fix it.

**Error Response (422):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "language"],
      "msg": "Input should be 'python' or 'javascript'"
    }
  ]
}
```

**Auth Failure (401):**
```json
{"detail": "Unauthorized"}
```

---

## Integration Examples

### JavaScript/React

```javascript
const executeCode = async (code, tests) => {
  const response = await fetch('http://localhost:7999/execute', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your_api_key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      language: 'python',
      exerciseId: 'my_exercise',
      code,
      tests
    })
  });
  
  const result = await response.json();
  
  if (result.passed) {
    console.log('✅ All tests passed!');
  } else {
    console.log(`❌ ${result.failedTests} test(s) failed`);
    console.log(result.error?.hint);
  }
  
  return result;
};
```

### Python

```python
import requests

response = requests.post(
    'http://localhost:7999/execute',
    headers={'X-API-Key': 'your_api_key'},
    json={
        'language': 'python',
        'exerciseId': 'my_exercise',
        'code': 'def add(a, b):\n  return a + b',
        'tests': 'def test_add():\n  assert add(1, 2) == 3'
    }
)

result = response.json()
print(f"Passed: {result['passed']}")
print(f"Tests: {result['passedTests']}/{result['totalTests']}")
```

---

## Configuration

### Environment Variables

**Required:**
- `EXECUTOR_API_KEY` - API key (min 32 chars, letters + numbers)

**CORS:**
- `CORS_ORIGINS` - Comma-separated allowed origins
  - Dev: `http://localhost:3000,http://localhost:8000`
  - Prod: `https://yourdomain.com,https://app.yourdomain.com`

**Optional:**
- `LOG_LEVEL` - INFO (default) | DEBUG
- `EXECUTION_TIMEOUT` - 1-30 seconds (default 5)
- `CONTAINER_MEMORY_MB` - Memory limit (default 512)
- `CONTAINER_CPU_LIMIT` - CPU cores (default 0.5)
- `HOST` - Bind address (default 0.0.0.0)
- `PORT` - Port (default 7999)

---

## Docker Isolation & Limits

Each execution runs in isolated container with:

| Limit | Value | Purpose |
|-------|-------|---------|
| Memory | 512 MB | Prevent runaway processes |
| CPU | 0.5 cores | Fair resource sharing |
| Timeout | 5s max | Prevent infinite loops |
| Network | Disabled | Prevent data exfiltration |
| Filesystem | Read-write `/workspace` only | Prevent host access |

---

## Security

- **API Key:** Required for all endpoints except `/health`
- **CORS:** Allowed origins configurable per environment
- **Validation:** All inputs validated (Pydantic)
- **Logging:** Code NEVER logged (only IDs, errors, metrics)
- **Headers:** Security headers on all responses

See [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) for details.

---

## Supported Languages

| Language | Status | Tests | Notes |
|----------|--------|-------|-------|
| Python | ✅ Ready | pytest | Full support |
| JavaScript | 🔄 Planned | jest | Coming soon |

---

## Troubleshooting

### 401 Unauthorized
- Check `X-API-Key` header matches `EXECUTOR_API_KEY`
- Verify health check works: `curl http://localhost:7999/health`

### 422 Validation Error
- Check `language` is `python` or `javascript`
- Check `exerciseId` matches `^[a-z0-9_]+$`
- Check `code` and `tests` are strings, < 1MB each

### 500 Internal Error
- Check Docker is running: `docker ps`
- Check container has Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`
- Check logs: `docker logs <container_id>`

### CORS Errors
- Add your origin to `CORS_ORIGINS` in `.env`
- Restart container after changing `.env`

---

## Next Steps

1. **Deploy** using Docker or local Python
2. **Test** with curl or Postman
3. **Integrate** using code examples above
4. **Monitor** via logs (JSON format, queryable)

See [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) for production setup.

---

[← Back to Scope Matrix](01_scope-matrix.md)
