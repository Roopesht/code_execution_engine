# Security Specification - Local Code Execution Engine

## Overview

This document specifies the security measures to prevent unauthorized access to the code execution API. The approach is intentionally simple and focused on preventing accidental/malicious external access.

---

## Threat Model

**Threats:**
- Unauthorized external websites trying to execute code
- Malicious programs attempting to use the API
- Code injection attacks
- Cross-site request forgery (CSRF)

**Assumptions:**
- Executor runs on student's local machine (localhost)
- Learning Platform on same machine or trusted network
- No public internet exposure

---

## Security Measures

### 1. API Key Authentication

**Implementation:**
- Require `X-API-Key` header in all requests
- Static API key configured at startup
- Simple header validation before processing

**Example Request:**
```bash
curl -X POST http://localhost:7999/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: executor_secret_key_12345" \
  -d '{...}'
```

**Configuration:**
```bash
# Environment variable
export EXECUTOR_API_KEY="executor_secret_key_12345"
```

**Validation:**
```python
# In FastAPI middleware
@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)  # Allow health check
    
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("EXECUTOR_API_KEY")
    
    if not api_key or api_key != expected_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"}
        )
    
    return await call_next(request)
```

---

### 2. CORS (Cross-Origin Resource Sharing)

**Implementation:**
- Allow requests only from Learning Platform origin
- Restrict preflight requests

**Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Learning Platform
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,
)
```

**Effect:**
- Browsers block requests from other origins
- Prevents accidental cross-site requests
- Does NOT protect against server-to-server attacks (use API key for that)

---

### 3. Health Check Exception

**Implementation:**
- `/health` endpoint does NOT require API key
- Allows Docker health checks
- Does NOT expose sensitive information

**Example:**
```bash
curl http://localhost:7999/health
# Response: {"status": "running"}
```

**Why:** 
- Health checks used by container orchestration
- Returns no sensitive data
- Simple way to verify service is running

---

### 4. Rate Limiting (Optional)

**Implementation:**
- Limit requests per IP address
- Prevent brute force attacks

**Configuration:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/execute")
@limiter.limit("100/minute")  # 100 requests per minute
async def execute(request: ExecutionRequest):
    ...
```

**Effect:**
- Prevents accidental DOS attacks
- Limits execution queue

---

### 5. Input Validation

**Implementation:**
- Validate all request fields
- Reject invalid syntax early
- Prevent injection attacks

**Validation Rules:**
- `language`: Must be exactly `"python"` or `"javascript"`
- `exerciseId`: Only alphanumeric + underscore
- `code`: Non-empty string (no command injection possible)
- `tests`: Non-empty string (executed in isolated container)

**Example:**
```python
class ExecutionRequest(BaseModel):
    language: Literal["python", "javascript"]
    exerciseId: str = Field(regex="^[a-z0-9_]+$", max_length=255)
    code: str = Field(min_length=1, max_length=1_000_000)
    tests: str = Field(min_length=1, max_length=1_000_000)
    timeout: int = Field(ge=1, le=30)
```

---

### 6. Isolation via Docker

**Implementation:**
- All code runs in isolated container
- No access to host filesystem
- No network access
- Resource limits enforced

**Benefits:**
- Even if attacker executes code, container isolation prevents host access
- Memory and CPU limits prevent resource exhaustion
- Container destroyed after execution

---

## Request/Response Flow with Security

```
1. External Request
   ↓
2. CORS Check
   ├─ ✅ Allowed origin → Continue
   └─ ❌ Blocked origin → Return 403
   ↓
3. API Key Validation
   ├─ ✅ Valid key → Continue
   └─ ❌ Invalid/Missing key → Return 401
   ↓
4. Input Validation
   ├─ ✅ Valid fields → Continue
   └─ ❌ Invalid fields → Return 422
   ↓
5. Execute in Docker
   ├─ Isolated container
   ├─ No filesystem access
   └─ Resource limits
   ↓
6. Return Response
   └─ Only execution results (no system info)
```

---

## HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| **200** | Execution completed | Successful or failed execution |
| **401** | Unauthorized | Missing/invalid API key |
| **403** | Forbidden | CORS origin not allowed |
| **422** | Validation error | Invalid request fields |
| **500** | Server error | Executor crash (should not happen) |

---

## Configuration Examples

### Docker Compose with API Key

```yaml
services:
  executor:
    build: .
    ports:
      - "7999:7999"
    environment:
      - EXECUTOR_API_KEY=your_secret_key_here
      - EXECUTOR_CORS_ORIGIN=http://localhost:3000
      - LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7999/health"]
```

### Learning Platform Request

```python
import requests

EXECUTOR_URL = "http://localhost:7999"
API_KEY = "your_secret_key_here"

def execute_code(language, code, tests, exercise_id):
    response = requests.post(
        f"{EXECUTOR_URL}/execute",
        json={
            "language": language,
            "code": code,
            "tests": tests,
            "exerciseId": exercise_id
        },
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
    )
    return response.json()
```

---

## Security Checklist

- [ ] API Key configured and stored securely
- [ ] CORS origins restricted to Learning Platform
- [ ] Health check works without API key
- [ ] Invalid API keys return 401
- [ ] CORS blocks external origins
- [ ] Input validation rejects invalid fields
- [ ] Code executes in isolated Docker container
- [ ] Container has no filesystem access
- [ ] Container has resource limits
- [ ] Logs don't contain sensitive data (user code)
- [ ] Rate limiting configured (optional)

---

## Limitations & Future Enhancements

**Current Approach:**
- ✅ Prevents most unauthorized external access
- ✅ Simple to implement and maintain
- ✅ Suitable for local/trusted network

**Limitations:**
- ❌ API key in plaintext (not for public internet)
- ❌ No authentication for specific users
- ❌ No audit logging of who ran what
- ❌ No request signing

**Future Enhancements:**
- OAuth 2.0 for user-level access control
- JWT tokens instead of static API key
- Request signing and verification
- Comprehensive audit logging
- Certificate-based mTLS authentication
- API key rotation policies

---

[← Back to Scope Matrix](01_scope-matrix.md)
