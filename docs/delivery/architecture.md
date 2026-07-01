# Architecture - Local Code Execution Engine

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│           Learning Platform / Client                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP (REST API)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Executor Server (localhost:7999)                  │
│  ├── Health Check Endpoint (/health)                        │
│  ├── Execution Endpoint (/execute)                          │
│  ├── Request Validation                                     │
│  └── Response Formatting                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│ Python Executor  │         │ JS Executor      │
│  • prepare()     │         │  • prepare()     │
│  • execute()     │         │  • execute()     │
│  • collect()     │         │  • collect()     │
│  • cleanup()     │         │  • cleanup()     │
└────────┬─────────┘         └────────┬─────────┘
         │                           │
         ▼                           ▼
┌──────────────────────┐   ┌──────────────────────┐
│ Python Docker Image  │   │ Node.js Docker Image │
│ with pytest          │   │ with jest/test lib   │
└──────────────────────┘   └──────────────────────┘
```

---

## Key Components

### 1. FastAPI Server
- Receives code execution requests
- Validates input
- Routes to appropriate executor
- Formats and returns results

### 2. Language Executors
- Abstract base executor class
- Language-specific implementations (Python, JavaScript)
- Common interface: `prepare()`, `execute()`, `collect_results()`, `cleanup()`

### 3. Docker Integration
- Isolation: Each execution runs in a fresh, disposable container
- Network: Containers have no external network access
- Resources: CPU and memory limits enforced
- Cleanup: Automatic removal after execution

---

## Design Principles

| Principle | Implementation |
|-----------|-----------------|
| **Isolation** | Each execution in its own Docker container |
| **Stateless** | No request depends on previous state |
| **Ephemeral** | All temporary files deleted after execution |
| **Modular** | Language support via pluggable executors |
| **Observable** | Comprehensive logging of execution details |
| **Secure** | No network access, resource limits, non-root execution |

---

## Execution Flow

```
1. Receive Request
   └─> Validate language, exerciseId, code

2. Route to Executor
   └─> Select Python or JavaScript executor

3. Prepare Environment
   └─> Create temp workspace
   └─> Write source code
   └─> Copy test files

4. Execute in Container
   └─> Start Docker container
   └─> Run tests (pytest/jest)
   └─> Capture output & metrics

5. Collect Results
   └─> Parse test results
   └─> Extract pass/fail counts
   └─> Record execution time & memory

6. Cleanup
   └─> Delete temp workspace
   └─> Stop & remove container

7. Return Response
   └─> Format JSON response
   └─> Return to client
```

---

## Directory Structure

```
executor/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application instance
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py        # /health, /execute routes
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py          # ExecutionRequest
│   │   └── response.py         # ExecutionResponse
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseExecutor abstract class
│   │   ├── python/
│   │   │   ├── __init__.py
│   │   │   └── executor.py     # PythonExecutor
│   │   └── javascript/
│   │       ├── __init__.py
│   │       └── executor.py     # JavaScriptExecutor
│   ├── services/
│   │   ├── __init__.py
│   │   └── execution.py        # ExecutionService (orchestration)
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging setup
│       └── docker_client.py    # Docker interaction
│
├── docker/
│   ├── python/
│   │   └── Dockerfile          # Python 3.11 + pytest
│   └── javascript/
│       └── Dockerfile          # Node.js 20 + jest
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docker-compose.yml
├── requirements.txt
├── main.py                     # Entry point
└── README.md
```

---

## Security Architecture

```
REQUEST
   ↓
┌─────────────────────────────────────────┐
│ 1. CORS Middleware                      │
│    ├─ Check origin                      │
│    └─ Allow only Learning Platform      │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 2. API Key Validation                   │
│    ├─ Extract X-API-Key header          │
│    └─ Validate against environment      │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 3. Input Validation                     │
│    ├─ Validate language                 │
│    ├─ Validate exerciseId               │
│    ├─ Validate code length              │
│    ├─ Validate tests format             │
│    └─ Reject invalid requests (422)     │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 4. Isolated Execution                   │
│    ├─ Fresh Docker container            │
│    ├─ No network access                 │
│    ├─ No host filesystem access         │
│    ├─ Resource limits (CPU, Memory)     │
│    └─ Timeout enforcement               │
└─────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────┐
│ 5. Safe Cleanup                         │
│    ├─ Delete temp workspace             │
│    ├─ Remove Docker container           │
│    └─ Free all resources                │
└─────────────────────────────────────────┘
   ↓
RESPONSE (no sensitive data exposed)
```

---

## Workspace & Ephemeral File Management

### Workspace Lifecycle

```
1. CREATE
   └─> /tmp/executor_<uuid>/
       ├─ user_code.py       (from request)
       └─ test_solution.py   (from request)

2. EXECUTE
   └─> Docker mounts workspace as /workspace/
       ├─ User code loaded into container
       ├─ Tests loaded into container
       └─ Tests import and execute user code

3. COLLECT
   └─> Parse test results
       ├─ Extract test names, status
       ├─ Collect stdout/stderr
       └─ Record metrics (time, memory)

4. CLEANUP
   └─> Delete workspace
       ├─ rm -rf /tmp/executor_<uuid>/
       └─ All files permanently removed
```

### Ephemeral Data Handling

- ✅ User code NOT stored after execution
- ✅ Test results NOT stored persistently
- ✅ Temporary files deleted within milliseconds
- ✅ No recovery/audit trail of submissions
- ✅ Only JSON response returned to Learning Platform

---

## Error Handling Architecture

```
EXECUTION ERROR HANDLING

Syntax Error
  └─> Detected during code compilation
      ├─ Return 200 with error details
      └─ Tests: 0/0, error type & message

Runtime Error
  └─> Detected during test execution
      ├─ Catch exception in Docker
      ├─ Capture full stack trace
      └─ Return 200 with error & stack trace

Timeout Error
  └─> Execution exceeds timeout
      ├─ Container killed after N seconds
      ├─ Return 200 with TimeoutError
      └─ Metrics show full timeout duration

Import Error
  └─> Missing dependency or module
      ├─ Caught before test execution
      └─ Return 200 with ImportError

Validation Error
  └─> Invalid request format
      ├─ Return 422 with validation details
      └─ No execution attempted
```

---

## Concurrency Considerations

### Sequential Execution (v1)

```
Request 1 ──────────────────────────┐
                                    └─> FastAPI Queue ─> Process ─> Response
Request 2 ──────────────────────────┐
                                    └─> (waits)
Request 3 ──────────────────────────┐
                                    └─> (waits)
```

**Current Design:**
- Sequential processing (one at a time)
- Each request waits for Docker container to finish
- Simple to implement and reason about
- Suitable for local/single-user scenarios

**Future Enhancement:**
- Parallel execution with worker pool
- Queue-based task distribution
- Multiple concurrent containers
- Load balancing across workers

---

## Extension Points

### Adding a New Language

To add support for a new language (e.g., Java):

1. Create `app/executors/java/executor.py`
2. Implement `JavaExecutor` class with required interface
3. Create `docker/java/Dockerfile`
4. Register in executor factory
5. Add test fixtures

No changes needed to core API or FastAPI server.

### Adding New API Endpoints

Add routes to `app/api/endpoints.py`:
- `/stats` - Execution statistics
- `/health/detailed` - Detailed health check
- `/version` - API version

Base architecture remains unchanged.

---

[← Back to Scope Matrix](01_scope-matrix.md)
