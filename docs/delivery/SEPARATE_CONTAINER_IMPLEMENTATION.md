# Separate Container Architecture - Implementation Guide

[← Back to Scope Matrix](01_scope-matrix.md)

---

## Overview

Migrate from single controller container to separate language-specific executor containers, each with its own FastAPI server.

**Port Mapping:**
- **Port 7998:** Python Executor (`code-executor-python`)
- **Port 7996:** JavaScript Executor (`code-executor-javascript`)
- **Port 7994:** React Executor (`code-executor-react`)

Each container runs the same API, only executor implementation differs.

---

## Architecture

```
Client Request
    ↓
Determine Language
    ↓
┌─────────────────────────────┐
│ if language == "python"     │
│   → http://localhost:7998   │
├─────────────────────────────┤
│ if language == "javascript" │
│   → http://localhost:7996   │
├─────────────────────────────┤
│ if language == "react"      │
│   → http://localhost:7994   │
└─────────────────────────────┘
    ↓
POST /execute (identical API)
    ↓
Language-specific Executor
(Python/JavaScript/React)
    ↓
Sequential execution (async lock)
    ↓
Response (200 OK or 4xx/5xx per Story 3.2.1)
```

---

## Docker Compose Setup

### docker-compose.yml

```yaml
version: '3.8'

services:
  code-executor-python:
    build:
      context: .
      dockerfile: Dockerfile.executor.python
    container_name: code-executor-python
    ports:
      - "7998:7999"
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=python
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-5}
      - HOST=localhost
      - PORT=7999
      - HTTPS_PORT=7998
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped

  code-executor-javascript:
    build:
      context: .
      dockerfile: Dockerfile.executor.javascript
    container_name: code-executor-javascript
    ports:
      - "7996:7999"
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=javascript
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-5}
      - HOST=localhost
      - PORT=7999
      - HTTPS_PORT=7996
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped

  code-executor-react:
    build:
      context: .
      dockerfile: Dockerfile.executor.react
    container_name: code-executor-react
    ports:
      - "7994:7999"
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=react
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-10}
      - HOST=localhost
      - PORT=7999
      - HTTPS_PORT=7994
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped
```

---

## Dockerfiles

### Dockerfile.executor.python

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add pytest for Python tests
RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-cov==4.1.0 \
    pytest-timeout==2.2.0

COPY src/ ./src/
COPY run_api.py .

EXPOSE 7999

ENV EXECUTOR_LANGUAGE=python

CMD ["python", "run_api.py"]
```

### Dockerfile.executor.javascript

```dockerfile
FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Node dependencies for JavaScript
RUN npm install -g --silent \
    jest@29.7.0 \
    mocha@10.2.0 \
    chai@4.3.10

COPY requirements.txt .
RUN apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_api.py .

EXPOSE 7999

ENV EXECUTOR_LANGUAGE=javascript

CMD ["python3", "run_api.py"]
```

### Dockerfile.executor.react

```dockerfile
FROM node:20-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# React testing dependencies
RUN npm install -g --silent \
    jest@29.7.0 \
    @testing-library/react@14 \
    react@18 \
    react-dom@18 \
    playwright@1.40.1

COPY requirements.txt .
RUN apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_api.py .

EXPOSE 7999

ENV EXECUTOR_LANGUAGE=react

CMD ["python3", "run_api.py"]
```

---

## Application Code Changes

### src/app/services/execution.py

Instantiate executor based on `EXECUTOR_LANGUAGE` env var:

```python
import os
from ..executors.python import PythonExecutor
from ..executors.javascript import JavaScriptExecutor
from ..executors.react import ReactExecutor

def get_executor(language: str):
    """Get executor based on language"""
    executors = {
        "python": PythonExecutor,
        "javascript": JavaScriptExecutor,
        "react": ReactExecutor,
    }
    
    executor_class = executors.get(language)
    if not executor_class:
        raise ValueError(f"Unsupported language: {language}")
    
    return executor_class()

async def execute_code(request: ExecutionRequest) -> ExecutionResponse:
    """Execute code and return results"""
    # Determine language from EXECUTOR_LANGUAGE env or request
    language = os.getenv("EXECUTOR_LANGUAGE", request.language)
    
    executor = get_executor(language)
    # ... rest of execution logic
```

---

## Client-Side Routing

### Example: Python Client

```python
import requests

class CodeExecutor:
    def __init__(self):
        self.executors = {
            "python": "http://localhost:7998",
            "javascript": "http://localhost:7996",
            "react": "http://localhost:7994",
        }
        self.api_key = os.getenv("EXECUTOR_API_KEY")
    
    def execute(self, language: str, code: str, tests: str):
        """Execute code on appropriate executor"""
        url = f"{self.executors[language]}/execute"
        
        response = requests.post(
            url,
            json={
                "language": language,
                "exerciseId": "test-id",
                "code": code,
                "tests": tests
            },
            headers={"X-API-Key": self.api_key}
        )
        
        return response.json()

# Usage
executor = CodeExecutor()
result = executor.execute("python", "def foo(): return 42", "def test_foo(): assert foo() == 42")
```

---

## Workspace Isolation

Each container has its own `/tmp/` directory:

```
Container 1 (Python):
  /tmp/executor_<uuid1>/
    └── test_solution.py

Container 2 (JavaScript):
  /tmp/executor_<uuid2>/
    └── test_solution.js

Container 3 (React):
  /tmp/executor_<uuid3>/
    └── test_solution.jsx
```

**No cross-contamination:** Files in one container don't affect others.

---

## Sequential Execution

Each container maintains its own execution lock (`docker_execution_lock` in `docker_client.py`):

```
Request 1 (Python) ─────┐
                        ├─→ Python Container Lock ─→ Execute ─→ Response
Request 2 (Python) ─────┤   (one at a time)
                        └─→ (waits)

Request 3 (JS) ─────────┐
                        ├─→ JS Container Lock ─→ Execute ─→ Response
Request 4 (JS) ─────────┤   (independent from Python)
                        └─→ (waits)
```

**Important:** Each container is sequential, but containers can execute in parallel.

---

## Error Response Format (Story 3.2.1)

All containers return consistent error responses:

### HTTP Status Codes

| Scenario | Code | Response |
|----------|------|----------|
| Missing API key | 401 | `{"status": "error", "code": "UNAUTHORIZED", ...}` |
| Invalid JSON | 400 | `{"status": "error", "code": "INVALID_REQUEST", ...}` |
| Unsupported language | 400 | `{"status": "error", "code": "UNSUPPORTED_LANGUAGE", ...}` |
| Timeout | 500 | `{"status": "error", "code": "TIMEOUT", ...}` |
| Docker/system error | 500 | `{"status": "error", "code": "INTERNAL_ERROR", ...}` |
| Execution error (test failed) | 200 | `{"status": "success", "execution_error": "...", ...}` |

### Response Format

```python
# Success with passing tests
{
    "status": "success",
    "language": "python",
    "passed": True,
    "totalTests": 3,
    "passedTests": 3,
    "failedTests": 0,
    "executionTime": 0.45,
    "tests": [...],
    "stdout": "..."
}

# Success with failing tests
{
    "status": "success",
    "language": "python",
    "passed": False,
    "totalTests": 3,
    "passedTests": 2,
    "failedTests": 1,
    "executionTime": 0.32,
    "tests": [...],
    "stdout": "...",
    "execution_error": "AssertionError: expected 10, got 5"
}

# Client error (400)
{
    "status": "error",
    "code": "INVALID_REQUEST",
    "error": "Bad Request: Missing 'code' field",
    "details": {"field": "code", "reason": "required"}
}

# Server error (500)
{
    "status": "error",
    "code": "INTERNAL_ERROR",
    "error": "Internal Server Error: Container timeout after 5s",
    "details": {"timeout": 5, "language": "python"}
}
```

---

## Migration Checklist

- [ ] Rename root `Dockerfile` → `Dockerfile.executor.python`
- [ ] Create `Dockerfile.executor.javascript` from `src/docker/javascript/Dockerfile`
- [ ] Create `Dockerfile.executor.react` (new)
- [ ] Update `docker-compose.yml` with 3 services
- [ ] Add `EXECUTOR_LANGUAGE` env var to each service
- [ ] Update `src/app/services/execution.py` to use env var
- [ ] Create `JavaScriptExecutor` class
- [ ] Create `ReactExecutor` class
- [ ] Implement Story 3.2.1 error response format
- [ ] Update `.env` and `.env.example` with 3 ports
- [ ] Test each container independently
- [ ] Update integration tests
- [ ] Update API documentation
- [ ] Update deployment guide

---

## Testing Strategy

### Unit Tests
- Each executor independently
- Test timeout handling
- Test error parsing

### Integration Tests
- Python → Port 7998
- JavaScript → Port 7996
- React → Port 7994
- Error scenarios (401, 400, 500)
- Sequential execution (request queuing)

### End-to-End Tests
- Multi-container setup via docker-compose
- Concurrent requests to different containers
- Workspace isolation verification

---

[← Back to Scope Matrix](01_scope-matrix.md)
