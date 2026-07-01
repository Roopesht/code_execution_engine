# Implementation Decisions Reference

**Purpose:** Record all architectural choices made. Easy to review and change if needed.  
**Date:** 2026-07-01

---

## 1. API Key Authentication

**Decision:** Environment variable only (required) - no default in code  
**Why:** Secure by default, forces explicit setup, prevents accidental key leakage  
**Code Reference:** [code_examples/01_auth.py](code_examples/01_auth.py)  
**Exception:** `/health` endpoint exempt from auth

---

## 2. Logging Format

**Decision:** JSON structured logging to stdout  
**Why:** Machine-parseable for monitoring/aggregation, Docker-friendly, production-ready  
**Code Reference:** [code_examples/02_logger.py](code_examples/02_logger.py)  
**Alternative Rejected:** Console only (too basic), file-based (hard to manage in containers)

---

## 3. Concurrency Model

**Decision:** FastAPI async + Docker sequential execution with Lock  
**Why:** Handle multiple HTTP requests concurrently, but serialize Docker executions (resource constraint)  
**Docker Lock Pattern:** [code_examples/05_patterns.py L26-32](code_examples/05_patterns.py)  
**Future:** Parallel execution via worker pool when needed

---

## 4. Error Handling Approach

**Decision:** FastAPI defaults for validation errors (422), custom ExecutionResponse for execution results (200)  
**Why:** Minimal code, standard responses, clear separation of API errors vs. execution outcomes  
**HTTP Status Map:** 200=execution result, 401=auth fail, 403=CORS fail, 422=validation fail, 500=server error  
**Code Reference:** [code_examples/05_patterns.py L69-84](code_examples/05_patterns.py)

---

## 5. Docker Resource Limits

**Decision:** Memory=512MB, CPU=0.5, Timeout=5s, Network=disabled  
**Why:** Prevent resource exhaustion from runaway user code, balanced for local dev use  
**Alternative:** Unlimited (unsafe), 256MB (too tight), 1000MB (excessive for local)

---

## 6. Environment Variables

**Decision:** Required: `EXECUTOR_API_KEY` | Optional: `LOG_LEVEL`, `EXECUTION_TIMEOUT`, `CONTAINER_MEMORY_MB`, `CONTAINER_CPU_LIMIT`, `HOST`, `PORT`  
**Why:** Centralize configuration, secure secrets, allow flexibility without code changes  
**Code Reference:** [code_examples/03_config.py](code_examples/03_config.py)

---

## 7. File Handling Encoding

**Decision:** Always UTF-8 for code/test files  
**Why:** Support international characters, match Python 3 default  
**Pattern:** [code_examples/05_patterns.py L72-79](code_examples/05_patterns.py)

---

## 8. Workspace Management

**Decision:** `/tmp/executor_{uuid}/` created per request, deleted after execution (even on error)  
**Why:** Isolation, automatic cleanup, prevent disk leaks  
**Cleanup Pattern:** [code_examples/05_patterns.py L28-40](code_examples/05_patterns.py) (try/finally)

---

## 9. Code Organization

**Decision:** Modular structure: api → services → executors, config at module level  
**Why:** Avoid circular imports, clear dependency flow, testable components  
**Structure:** [QUICK_REFERENCE.md Code Organization](QUICK_REFERENCE.md#code-organization)

---

## Changes Made & Reversible Decisions

| What | Chosen | Alternative | Impact |
|------|--------|-------------|--------|
| API Key | ENV only | Hard-coded default | Can change in config.py |
| Logging | JSON | Console only | Can change JSONFormatter in logger.py |
| Concurrency | Sequential Docker | Parallel (future) | Can add worker pool later |
| Memory Limit | 512MB | 256MB or 1000MB | Can change in docker_client.py |
| CPU Limit | 0.5 | 0.25 or 1.0 | Can change in docker_client.py |
| Timeout | 5s | 3s or 10s | Can change in config.py |

---

**How to Change a Decision:**
1. Update decision in this file (explain why)
2. Update code_examples/ if pattern changes
3. Update QUICK_REFERENCE.md if needed
4. Notify team of change

---

[← Back to Scope Matrix](01_scope-matrix.md)
