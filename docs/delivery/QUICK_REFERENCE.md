# Implementation Guide - Decisions & Patterns

**Created:** 2026-07-01 | **Status:** Active for Phase 1+

---

## Global Decisions

Apply **across all 15 stories**. Reference code examples in `code_examples/` folder.

### 1. API Key Authentication
- **Decision:** Environment variable only (required)
- **No default** in code for security
- Health check (`/health`) exempt from auth
- Invalid key → 401 Unauthorized
- **Code:** [code_examples/01_auth.py](code_examples/01_auth.py)

### 2. Logging Strategy
- **Decision:** JSON structured logging (machine-parseable)
- All logs to stdout (Docker-friendly)
- Include: timestamp, level, logger, message, module, function, line
- Log events: REQUEST_RECEIVED, API_KEY_VALIDATION, EXECUTION_STARTED, DOCKER_*, RESPONSE_SENT
- **Code:** [code_examples/02_logger.py](code_examples/02_logger.py)

### 3. Concurrency Model
- **Decision:** Async/concurrent ready (FastAPI async)
- Docker execution: **sequential** (one at a time, use Lock)
- FastAPI handles multiple HTTP requests concurrently
- Requests queue for Docker availability
- Future: Worker pool for parallel execution
- **Pattern:** [code_examples/05_patterns.py](code_examples/05_patterns.py#L26-L32)

### 4. Error Handling
- **Decision:** FastAPI defaults for validation, custom for execution
- 200: Execution completed (pass/fail)
- 401: Unauthorized (missing/invalid API key)
- 403: Forbidden (CORS origin not allowed)
- 422: Validation error (FastAPI auto-generated)
- 500: Server error (should not happen)
- **Pattern:** [code_examples/05_patterns.py](code_examples/05_patterns.py#L69-L84)

---

## Code Organization

### Directory Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI app + middleware
├── api/endpoints.py        # Route handlers
├── models/                 # Request/Response models
├── executors/              # BaseExecutor + implementations
├── services/execution.py   # Orchestration
└── utils/
    ├── auth.py            # See code_examples/01_auth.py
    ├── logger.py          # See code_examples/02_logger.py
    ├── config.py          # See code_examples/03_config.py
    └── docker_client.py   # See code_examples/04_docker_client.py
```

### Import Order
- Services depend on models & executors
- API endpoints depend on services
- Main imports setup (no circular imports)

---

## Configuration

**Environment Variables:**

```bash
# Required
EXECUTOR_API_KEY=your_secret_key_here

# Optional (defaults shown)
LOG_LEVEL=INFO
EXECUTION_TIMEOUT=5
CONTAINER_MEMORY_MB=1024
CONTAINER_CPU_LIMIT=1
HOST=0.0.0.0
PORT=7999
```

**Code:** [code_examples/03_config.py](code_examples/03_config.py)

---

## Docker Integration

**Workspace:** `/tmp/executor_{uuid}/`
- `user_code.py` (from request)
- `test_solution.py` (from request)

**Resource Limits:**
- Memory: 1024 MB
- CPU: 1 (100% of one core)
- Timeout: 5 seconds (per request, configurable)
- Network: Disabled
- Filesystem: Read-write `/workspace` only

**Code:** [code_examples/04_docker_client.py](code_examples/04_docker_client.py)

---

## Implementation Patterns

All patterns in one file: [code_examples/05_patterns.py](code_examples/05_patterns.py)

| Pattern | Use Case |
|---------|----------|
| Logging | Structured JSON events |
| Cleanup | Always in `finally` block |
| Concurrency | Docker lock for sequential execution |
| Async Endpoint | validate → prepare → execute → cleanup |
| File Handling | UTF-8 encoding for code/tests |
| Error Response | 200 with error details |
| Middleware | API key validation |

---

## File Handling

**Encoding:** Always UTF-8

**Cleanup:** Always in `finally` block, even on error

**Pattern:** [code_examples/05_patterns.py](code_examples/05_patterns.py#L28-L40)

---

## Testing Strategy

**Unit Tests (Phase 1):**
- Pydantic model validation
- API key validation
- Error response format

**Integration Tests (Phase 3):**
- Complete request → response cycle
- Docker container creation/cleanup
- Error scenarios

---

## Security Checklist

- [ ] API key required (except /health)
- [ ] CORS configured
- [ ] Input validation on all fields
- [ ] No code in logs
- [ ] Docker: no network, read-only host
- [ ] Resource limits enforced
- [ ] Cleanup on error (try/finally)

---

## Performance Targets

```
Validation:        ~10ms
Docker startup:   ~500ms
Code execution:   ~200-500ms
Result parsing:   ~50ms
Cleanup:          ~100ms
───────────────────────────
Total (typical):  <2000ms
Max (timeout):    5000ms
```

---

## Deployment Checklist

Before Phase 2:
- [ ] All code committed
- [ ] Tests passing
- [ ] Docker images buildable
- [ ] docker-compose.yml tested
- [ ] Environment variables documented
- [ ] API key mechanism working
- [ ] Logging working
- [ ] Error handling tested

---

## Related Documentation

- [Stories](stories/) - Implementation tasks
- [architecture.md](architecture.md) - System design
- [security-specification.md](security-specification.md) - Security details
- [input-output-spec.md](input-output-spec.md) - API contract

---

[← Back to Scope Matrix](01_scope-matrix.md)
