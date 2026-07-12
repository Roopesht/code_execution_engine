# LLM Service Endpoints - Complete Usage Guide

[← Back to Scope Matrix](01_scope-matrix.md)

---

## Overview

Local LLM service runs on **port 8001** with OpenAI-compatible API. Two endpoints:

1. **`GET /health`** — Service health & model status
2. **`POST /v1/chat/completions`** — AI chat completions (OpenAI compatible)
3. **`POST /feedback`** — Student code feedback (executor endpoint)

---

## Endpoint 1: Health Check

**Endpoint:** `GET /health`

**Purpose:** Check service health and active model

### Request

```bash
curl http://localhost:8001/health
```

### Success Response (200 OK)

```json
{
  "status": "healthy",
  "model": {
    "id": "qwen2.5-coder-3b-v2",
    "filename": "qwen2.5-coder-3b-v2.gguf",
    "size_mb": 3400,
    "parameterCount": 3000000000,
    "version": "2.0",
    "contextSize": 8192,
    "quantization": "Q4_K_M"
  },
  "loaded": true,
  "uptime_seconds": 12345,
  "threads": 8,
  "hardware": {
    "gpu_available": true,
    "gpu_type": "CUDA",
    "memory_used_mb": 2048,
    "memory_total_mb": 8192
  },
  "startup_time_seconds": 4.567,
  "api_version": "v1"
}
```

### Error Responses

**503 Service Unavailable** (Service not running)
```json
{
  "status": "error",
  "error": "Service not responding",
  "code": "SERVICE_UNAVAILABLE"
}
```

**500 Model Not Loaded**
```json
{
  "status": "error",
  "error": "Model failed to load during startup",
  "code": "MODEL_LOAD_FAILED",
  "details": {
    "model": "qwen2.5-coder-3b-v2",
    "reason": "File not found or corrupted"
  }
}
```

---

## Endpoint 2: Chat Completions (OpenAI Compatible)

**Endpoint:** `POST /v1/chat/completions`

**Purpose:** Get AI completions for prompts (OpenAI API)

### Request

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {
        "role": "system",
        "content": "You are a Python code reviewer."
      },
      {
        "role": "user",
        "content": "Review this code: def foo(): return 42"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 150,
    "top_p": 0.9
  }'
```

### Request Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `model` | string | Yes | Use: `"qwen"` (model name is ignored, uses active model) |
| `messages` | array | Yes | Array of message objects with `role` and `content` |
| `temperature` | float | No | 0.0-2.0, default 0.2 (lower = more deterministic) |
| `max_tokens` | int | No | Max output tokens, default 150 |
| `top_p` | float | No | 0.0-1.0, default 0.9 (nucleus sampling) |
| `top_k` | int | No | Default 40 |

### Success Response (200 OK)

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1720598400,
  "model": "qwen2.5-coder-3b-v2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Your implementation is clean and correct. Consider adding docstrings and type hints for better documentation."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 23,
    "total_tokens": 68
  }
}
```

### Error Responses

**400 Bad Request** (Invalid format or missing fields)
```json
{
  "status": "error",
  "error": "Bad Request: Missing 'messages' field",
  "code": "INVALID_REQUEST",
  "details": {
    "field": "messages",
    "reason": "Required"
  }
}
```

**400 Bad Request** (Invalid message format)
```json
{
  "status": "error",
  "error": "Bad Request: Message must have 'role' and 'content'",
  "code": "INVALID_MESSAGE_FORMAT",
  "details": {
    "message_index": 0,
    "reason": "Missing 'role' field"
  }
}
```

**400 Bad Request** (Context length exceeded)
```json
{
  "status": "error",
  "error": "Bad Request: Prompt exceeds maximum context length (8192 tokens)",
  "code": "CONTEXT_LENGTH_EXCEEDED",
  "details": {
    "context_size": 8192,
    "prompt_tokens": 8500,
    "excess": 308
  }
}
```

**408 Request Timeout** (Generation took too long)
```json
{
  "status": "error",
  "error": "Request Timeout: Generation did not complete within 60 seconds",
  "code": "REQUEST_TIMEOUT",
  "details": {
    "timeout_seconds": 60
  }
}
```

**500 Internal Server Error** (LLM generation failed)
```json
{
  "status": "error",
  "error": "Internal Server Error: Model generation failed",
  "code": "GENERATION_FAILED",
  "details": {
    "reason": "Invalid prompt format"
  }
}
```

**503 Service Unavailable** (Model not loaded)
```json
{
  "status": "error",
  "error": "Service Unavailable: Model not loaded",
  "code": "MODEL_NOT_LOADED",
  "details": {
    "model": "qwen2.5-coder-3b-v2",
    "status": "loading"
  }
}
```

---

## Endpoint 3: Feedback (Executor Endpoint)

**Endpoint:** `POST /feedback`

**Purpose:** Get AI feedback on failed student code (on executor port 7998/7996/7994)

### Request

```bash
curl -X POST http://localhost:7998/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "language": "python",
    "exerciseId": "algo-sort",
    "studentCode": "def bubble_sort(arr):\n    return sorted(arr)",
    "failedTests": [
      {
        "name": "test_edge_case",
        "error": "AssertionError: expected [1,2,3], got [3,2,1]",
        "output": "Array not sorted correctly"
      }
    ],
    "compilerErrors": null,
    "staticAnalysis": [
      "Missing docstring",
      "No type hints"
    ]
  }'
```

### Request Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `language` | string | Yes | `"python"`, `"javascript"`, or `"react"` |
| `exerciseId` | string | Yes | Exercise identifier |
| `studentCode` | string | Yes | Student's code (max 2000 chars) |
| `failedTests` | array | Yes | Array of failed tests (min 1, max 5) |
| `compilerErrors` | string | No | Compilation/syntax errors |
| `staticAnalysis` | array | No | Code quality issues (max 10 items) |
| `problemDescription` | string | No | Original problem statement |

### Test Object Format

```json
{
  "name": "test_function_name",
  "error": "AssertionError: expected X, got Y",
  "output": "Additional output or stack trace"
}
```

### Success Response (200 OK)

```json
{
  "status": "success",
  "feedback": "Your sorting implementation looks good overall. The issue is that your code returns a new sorted array instead of modifying the original. Also consider adding input validation for edge cases like empty arrays or None values.",
  "model": "qwen2.5-coder-3b-v2",
  "tokens": {
    "prompt": 156,
    "completion": 45,
    "total": 201
  },
  "latency_ms": 234,
  "generatedAt": "2024-07-09T10:30:00Z"
}
```

### Error Responses

**400 Bad Request** (Missing required field)
```json
{
  "status": "error",
  "code": "INVALID_REQUEST",
  "error": "Bad Request: Missing 'studentCode' field",
  "details": {
    "field": "studentCode",
    "reason": "Required"
  }
}
```

**400 Bad Request** (Invalid language)
```json
{
  "status": "error",
  "code": "UNSUPPORTED_LANGUAGE",
  "error": "Bad Request: Unsupported language 'rust'. Supported: python, javascript, react",
  "details": {
    "language": "rust",
    "supported": ["python", "javascript", "react"]
  }
}
```

**400 Bad Request** (Code too long)
```json
{
  "status": "error",
  "code": "CODE_TOO_LONG",
  "error": "Bad Request: Student code exceeds maximum length (2000 characters)",
  "details": {
    "limit": 2000,
    "actual": 2500
  }
}
```

**400 Bad Request** (No failed tests)
```json
{
  "status": "error",
  "code": "NO_FAILED_TESTS",
  "error": "Bad Request: At least one failed test required",
  "details": {
    "count": 0
  }
}
```

**401 Unauthorized** (Missing/invalid API key)
```json
{
  "status": "error",
  "code": "UNAUTHORIZED",
  "error": "Unauthorized: Invalid or missing API key",
  "details": {
    "reason": "X-API-Key header missing or invalid"
  }
}
```

**500 Internal Server Error** (LLM service error)
```json
{
  "status": "error",
  "code": "LLM_ERROR",
  "error": "Internal Server Error: LLM generation failed",
  "details": {
    "reason": "Context length exceeded"
  }
}
```

**503 Service Unavailable** (LLM service not running)
```json
{
  "status": "error",
  "code": "LLM_UNAVAILABLE",
  "error": "Service Unavailable: LLM service unreachable on port 8001",
  "details": {
    "llm_port": 8001,
    "timeout_seconds": 30
  }
}
```

**504 Gateway Timeout** (LLM response took too long)
```json
{
  "status": "error",
  "code": "LLM_TIMEOUT",
  "error": "Gateway Timeout: LLM generation did not complete within 30 seconds",
  "details": {
    "timeout_seconds": 30,
    "language": "python"
  }
}
```

---

## Usage Examples

### Python Client

```python
import requests
import json

# Health check
response = requests.get("http://localhost:8001/health")
print(response.json())

# Chat completion
response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={
        "model": "qwen",
        "messages": [
            {"role": "system", "content": "You are a code reviewer."},
            {"role": "user", "content": "Review: def foo(): pass"}
        ],
        "temperature": 0.2,
        "max_tokens": 150
    }
)
print(response.json())

# Feedback (on executor, not LLM port)
response = requests.post(
    "http://localhost:7998/feedback",
    headers={"X-API-Key": "your-key"},
    json={
        "language": "python",
        "exerciseId": "test",
        "studentCode": "def foo(): pass",
        "failedTests": [
            {
                "name": "test_foo",
                "error": "AssertionError",
                "output": "Test failed"
            }
        ]
    }
)
print(response.json())
```

### OpenAI Python SDK

```python
from openai import OpenAI

# Point to local LLM service
client = OpenAI(
    api_key="dummy",  # Not needed for local service
    base_url="http://localhost:8001/v1"
)

# Use just like OpenAI API
response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "system", "content": "You are a Python expert."},
        {"role": "user", "content": "How to optimize this code?"}
    ],
    temperature=0.2,
    max_tokens=200
)

print(response.choices[0].message.content)
```

### JavaScript/Node.js

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "dummy",
  baseURL: "http://localhost:8001/v1"
});

async function getFeedback() {
  const response = await client.chat.completions.create({
    model: "qwen",
    messages: [
      {
        role: "system",
        content: "You are a JavaScript code reviewer."
      },
      {
        role: "user",
        content: "Review this code: const foo = () => 42;"
      }
    ],
    temperature: 0.2,
    max_tokens: 200
  });

  console.log(response.choices[0].message.content);
}

getFeedback();
```

### cURL Examples

**Health Check**
```bash
curl http://localhost:8001/health
```

**Chat Completion**
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

**Get Feedback**
```bash
curl -X POST http://localhost:7998/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "language": "python",
    "exerciseId": "test",
    "studentCode": "pass",
    "failedTests": [{"name": "t1", "error": "failed", "output": ""}]
  }'
```

---

## Error Handling Best Practices

### Check Status Code

```python
response = requests.post(...)

if response.status_code == 200:
    # Success
    result = response.json()
elif response.status_code == 400:
    # Client error - check your request
    error = response.json()
    print(f"Invalid request: {error['error']}")
elif response.status_code == 503:
    # LLM service not running - retry later
    error = response.json()
    print(f"Service unavailable: {error['error']}")
else:
    # Other error
    print(f"Error: {response.status_code}")
```

### Retry Logic

```python
import time
from requests.exceptions import ConnectionError

def call_llm_with_retry(url, json_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=json_data, timeout=30)
            
            if response.status_code == 503:
                # Service unavailable, retry
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise Exception("LLM service unavailable after retries")
            
            if response.status_code == 400:
                # Client error, don't retry
                raise ValueError(response.json()['error'])
            
            response.raise_for_status()
            return response.json()
            
        except ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise

    raise Exception("Max retries exceeded")
```

---

## Common Issues & Solutions

### Issue: 503 Service Unavailable

**Cause:** LLM service not running

**Solution:**
```bash
# Check service
docker ps | grep llm-server

# Start service
docker-compose up -d llm-server

# Check logs
docker logs llm-server
```

### Issue: 400 Context Length Exceeded

**Cause:** Prompt too long for model

**Solution:**
- Reduce student code length
- Use smaller model (1.5B instead of 3B)
- Truncate error messages

### Issue: 504 Timeout

**Cause:** Model taking too long to generate

**Solution:**
- Reduce `max_tokens`
- Lower `temperature` (faster, more deterministic)
- Use smaller model
- Increase timeout in your client

### Issue: Model Not Loaded

**Cause:** Wrong model selected in config

**Solution:**
```bash
# Check current model
curl http://localhost:8001/health | jq '.model.id'

# Check available models
cat lms/models/manifest.json | jq '.availableModels'

# Update model and rebuild
echo "LLM_MODEL_NAME=qwen2.5-coder-3b-v2" > .env
docker-compose build llm-server
docker-compose up -d llm-server
```

---

## Configuration Reference

### Environment Variables

```
LLM_SERVICE_URL=http://llm-server:8001
LLM_SERVICE_TIMEOUT=30
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=150
LLM_TOP_P=0.9
```

### LLM Server Config

```json
{
  "model": "active.gguf",
  "host": "0.0.0.0",
  "port": 8001,
  "threads": "auto",
  "context_size": 8192,
  "temperature": 0.2,
  "top_p": 0.9,
  "top_k": 40,
  "max_tokens": 150,
  "parallel": 2,
  "cache_type_k": "q8_0",
  "cache_type_v": "q8_0"
}
```

---

## Performance Metrics

### Expected Latency

| Operation | Time |
|-----------|------|
| Health check | < 10ms |
| Chat completion (50 tokens) | 300-500ms |
| Chat completion (150 tokens) | 500-1000ms |
| Feedback (45 prompt, 23 completion) | 200-400ms |

### Resource Usage

| Model | RAM | VRAM | Threads |
|-------|-----|------|---------|
| Qwen 3B | 8GB | 2GB (GPU) | 8 |
| Qwen 1.5B | 4GB | 1GB (GPU) | 8 |
| CPU Mode | 4GB | N/A | 4 |

---

[← Back to Scope Matrix](01_scope-matrix.md)
