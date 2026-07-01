# Security Configuration - Local Code Execution Engine

**Status:** Implemented  
**Date:** 2026-07-01

---

## Overview

The execution engine implements multi-layer security to prevent unauthorized access and protect system resources.

---

## Authentication

### API Key Authentication
- **Method:** X-API-Key header
- **Source:** `EXECUTOR_API_KEY` environment variable
- **Scope:** All endpoints except `/health`
- **Failure Response:** 401 Unauthorized
- **Implementation:** [src/app/utils/auth.py](../src/app/utils/auth.py)

### Health Check Exception
- **Endpoint:** `GET /health`
- **Authentication:** Not required
- **Purpose:** Service availability monitoring
- **Response:** `{"status": "running"}`

---

## Cross-Origin Resource Sharing (CORS)

### Allowed Origins
```
http://localhost:3000   # Development frontend
http://localhost:8000   # Development API
```

### Allowed Methods
- GET (read-only operations)
- POST (code execution)

### Allowed Headers
- Content-Type
- X-API-Key

### Configuration
```python
CORSMiddleware(
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"]
)
```

**Note:** Cross-origin requests without allowed origins are blocked with CORS error.

---

## Input Validation

### Request Validation
All requests validated using Pydantic models:

**ExecutionRequest Fields:**
- `language`: Literal["python", "javascript"] (enum-only)
- `exerciseId`: alphanumeric + underscore (regex: `^[a-z0-9_]+$`)
- `code`: string, max 1MB
- `tests`: string, max 1MB
- `timeout`: integer, 1-30 seconds (optional, default 5)

**Invalid Requests:** Return 422 Unprocessable Entity with validation errors

### Implementation
- [src/app/models/execution.py](../src/app/models/execution.py) - Request/Response models
- FastAPI automatic validation on POST /execute

---

## Docker Isolation & Resource Limits

### Network Isolation
- **Network Mode:** Disabled (`network_disabled=True`)
- **Effect:** Container has NO internet access
- **Protection:** Prevents outbound data exfiltration

### Resource Limits
- **Memory:** 512MB max
- **CPU:** 0.5 cores max
- **Timeout:** 5 seconds max execution time
- **Filesystem:** Read-write `/workspace` only

### Implementation
- [src/app/utils/docker_client.py](../src/app/utils/docker_client.py)

---

## Security Headers

Automatic security headers added to all responses:

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME type sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | Enable browser XSS filter |
| Strict-Transport-Security | max-age=31536000 | Force HTTPS |

---

## Logging & Monitoring

### Request Logging
All HTTP requests logged with:
- Method (GET, POST)
- Path (/health, /execute)
- Status code (200, 401, 422, 500)
- Duration (milliseconds)
- Request ID (if provided)

### Execution Logging
Execution details logged without code:
- exerciseId (not code)
- language (python, javascript)
- duration
- passed/failed status
- error type (not full traceback in persistent logs)

### Protection: Code Never Logged
- User code never appears in logs
- Test code never appears in logs
- Only identifiers logged (exerciseId, language)
- Stack traces limited to error type + message

---

## Data Protection

### What is NOT Stored Persistently
- User code submissions
- Test code
- Execution output (stdout/stderr beyond immediate response)
- API keys in logs
- System information

### What IS Stored
- Request/response metadata (timestamps, status codes)
- Error summaries (type, message, not full stack)
- Performance metrics (duration, memory usage)

---

## Endpoint Security Summary

| Endpoint | Auth | Method | CORS | Validation | Status |
|----------|------|--------|------|-----------|--------|
| `/health` | ❌ No | GET | ✅ Yes | N/A | ✅ |
| `/execute` | ✅ Yes | POST | ✅ Yes | ✅ Strict | ✅ |
| `/docs` | ✅ Yes | GET | ✅ Yes | N/A | ✅ |

---

## Environment Variables

### Required
```bash
EXECUTOR_API_KEY=<secret_key>
```

### Optional
```bash
LOG_LEVEL=INFO              # Logging verbosity
EXECUTION_TIMEOUT=5         # Seconds
CONTAINER_MEMORY_MB=512     # MB
CONTAINER_CPU_LIMIT=0.5     # CPU cores
HOST=0.0.0.0               # Bind address
PORT=7999                  # Port
```

---

## Security Checklist

- [x] API key required for `/execute` endpoint
- [x] Missing/invalid API key returns 401
- [x] CORS configured for allowed origins only
- [x] Cross-origin requests blocked if not in allow list
- [x] Health check works without API key
- [x] All input fields validated (Pydantic)
- [x] Invalid inputs return 422
- [x] Docker containers have no network access
- [x] Docker containers have resource limits (memory, CPU, timeout)
- [x] No system information leaked in responses
- [x] Security headers added to all responses
- [x] User code never logged persistently
- [x] Security configuration documented

---

## Deployment Recommendations

1. **Change CORS origins** from localhost to your domain
2. **Use strong API key** (64+ characters, random)
3. **Rotate API key** regularly
4. **Monitor logs** for unauthorized access attempts
5. **Keep Docker updated** for security patches
6. **Run with least privilege** user account
7. **Enable HTTPS** in production (add reverse proxy)
8. **Rate limit** API calls (future enhancement)

---

## Language Compatibility

Security measures apply uniformly to both Python and JavaScript execution:
- Both use same Docker isolation
- Both have same resource limits
- Both follow same input validation
- Both get same security headers
- Both log in same format (no code)

---

[← Back to Scope Matrix](01_scope-matrix.md)
