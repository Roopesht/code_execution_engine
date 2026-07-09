# Docker Architecture Analysis & Recommendations

## Current State

**Today you have:**
1. **Main Dockerfile** (root) → FastAPI API Server/Controller
2. **src/docker/python/Dockerfile** → Python execution environment
3. **src/docker/javascript/Dockerfile** → JavaScript execution environment
4. **docker-compose.yml** → Only runs the controller

**Original Intent (from architecture.md):**
- Separate **controller** (API) from **executors** (language-specific)
- Each execution runs in its own fresh container

**Current Issue:** Implementation drifted; documentation doesn't match current setup.

---

## Proposed Architecture Options

### Option A: Language-Specific Executors (RECOMMENDED ✅)

**Structure:**
```
Images:
├── code-executor-api          (FastAPI controller)
├── code-executor-python       (Python 3.11 + pytest)
├── code-executor-javascript   (Node.js + jest)
├── code-executor-react        (React + testing library + sandbox)
└── code-executor-react-sandbox (Isolated React renderer)

docker-compose.yml:
├── api service                (always running)
├── python image               (spawned per request)
├── javascript image           (spawned per request)
├── react image                (spawned per request)
└── react-sandbox image        (spawned per request)
```

**Pros:**
- ✅ Minimal image size (each executor is ~500MB-1GB)
- ✅ Fast startup (only required deps installed)
- ✅ Independent updates (update Python without touching React)
- ✅ Easy to scale horizontally (spawn N containers)
- ✅ Clean separation of concerns
- ✅ Follows microservices principle

**Cons:**
- ⚠️ Requires orchestration (Docker or Kubernetes)
- ⚠️ More complex deployment (4 images to manage)

**Best For:** Production, multiple language support, scaling.

---

### Option B: Single Universal Image

**Structure:**
```
Images:
├── code-executor-api          (FastAPI controller)
└── code-executor-all          (Python + Node.js + React + all deps)
```

**Pros:**
- ✅ Simple deployment (1 image to build)
- ✅ Single docker-compose.yml
- ✅ Easier troubleshooting (all tools in one place)

**Cons:**
- ❌ Large image size (~2-3GB)
- ❌ Slower startup (all deps loaded)
- ❌ Updates affect all languages (atomic)
- ❌ Wastes resources (Python request loads Node.js)
- ❌ Hard to optimize per language
- ❌ Not scalable

**Best For:** Development only, single-language at a time.

---

### Option C: Hybrid (Moderate)

**Structure:**
```
Images:
├── code-executor-api          (FastAPI controller)
├── code-executor-languages    (Python + JavaScript + React)
└── code-executor-react-sandbox (Isolated React - separate)
```

**Pros:**
- ✅ Smaller images than Option B (~1.5GB)
- ✅ Simpler than Option A (2 images instead of 4)
- ✅ React sandbox isolated (security)

**Cons:**
- ⚠️ Still carries unused deps for some requests
- ⚠️ Less granular control

**Best For:** Mid-scale deployments.

---

## Recommendation: **Option A - Language-Specific Executors**

### Why?

1. **Scalability**: Spawn executor containers only when needed
2. **Efficiency**: Each image is optimized for its purpose
3. **Maintenance**: Update Python independently without rebuilding everything
4. **Safety**: React runs isolated in its own sandbox container
5. **Production-Ready**: Standard microservices pattern

### Implementation Timeline

```
Phase 1: Stabilize Current
  └─ Refactor existing Python/JS to Option A pattern
  └─ Update docker-compose to explicitly define all services
  └─ Update documentation

Phase 2: Add React Support
  └─ Create code-executor-react image
  └─ Create code-executor-react-sandbox image
  └─ Test isolation and security

Phase 3: Add Orchestration
  └─ Docker Swarm OR Kubernetes
  └─ Auto-scaling based on load
  └─ Health checks and monitoring
```

---

## Architecture: Option A (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│           Learning Platform / Client                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS (REST API)
                     ▼
        ┌────────────────────────────┐
        │ code-executor-api service  │
        │ (FastAPI, always running)  │
        └──────┬────────────────────┬┴──────┬─────────┐
               │                    │       │         │
        ┌──────▼────┐    ┌─────────▼──┐  ┌─▼───────┐ │
        │  Request  │    │  Request   │  │Request │ │
        │  Python   │    │ JavaScript │  │ React  │ │
        └──────┬────┘    └──────┬─────┘  └───┬────┘ │
               │                │            │      │
        ┌──────▼────────────────▼────────────▼──┐  │
        │  Docker Daemon (spawns containers)    │  │
        └──────┬────────┬───────────┬──────────┘  │
               │        │           │             │
        ┌──────▼─┐ ┌────▼────┐ ┌───▼───────┐    │
        │executor-│ │executor-│ │executor-  │    │
        │python   │ │jsnode   │ │react      │    │
        └────────┘ └─────────┘ └───┬───────┘    │
                                    │            │
                            ┌───────▼──────┐    │
                            │executor-     │    │
                            │react-sandbox │    │
                            └──────────────┘    │
                                                 │
        (All spawned & destroyed per request)   │
        (Isolated, no network access)           │
```

---

## Docker Setup: Option A (Recommended)

### Revised docker-compose.yml (Option B: Separate Containers)

```yaml
version: '3.8'

services:
  # Python Executor - Port 7998
  code-executor-python:
    build:
      context: .
      dockerfile: Dockerfile.executor.python
    container_name: code-executor-python
    ports:
      - "7998:7999"  # Container port 7999 → Host port 7998
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=python
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-5}
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped

  # JavaScript Executor - Port 7996
  code-executor-javascript:
    build:
      context: .
      dockerfile: Dockerfile.executor.javascript
    container_name: code-executor-javascript
    ports:
      - "7996:7999"  # Container port 7999 → Host port 7996
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=javascript
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-5}
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped

  # React Executor - Port 7994
  code-executor-react:
    build:
      context: .
      dockerfile: Dockerfile.executor.react
    container_name: code-executor-react
    ports:
      - "7994:7999"  # Container port 7999 → Host port 7994
    environment:
      - EXECUTOR_API_KEY=${EXECUTOR_API_KEY}
      - EXECUTOR_LANGUAGE=react
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - EXECUTION_TIMEOUT=${EXECUTION_TIMEOUT:-10}  # React tests may take longer
    volumes:
      - ./certs:/app/certs:ro
    restart: unless-stopped
```

**Key Points:**
- Each container runs its own FastAPI server on internal port 7999
- Host ports are different (7998, 7996, 7994)
- Each has identical API (`/health`, `/execute`)
- Executor implementation varies (Python, JavaScript, React)
- Client routes based on language (Python → 7998, JS → 7996, React → 7994)

### Dockerfile Structure (All Executors Identical API)

Each executor container (Python, JS, React) runs the same FastAPI server code:

```dockerfile
# Dockerfile.executor.python
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_api.py .

EXPOSE 7999

ENV EXECUTOR_LANGUAGE=python

CMD ["python", "run_api.py"]
```

**Key:**
- Same `src/app/main.py` (FastAPI server)
- Same `/execute` endpoint signature
- `EXECUTOR_LANGUAGE` env var tells API which executor to instantiate
- Only dependencies differ (pytest for Python, jest for JS, etc.)

### Dockerfile.executor.python

```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest==7.4.3 \
    pytest-cov==4.1.0 \
    pytest-timeout==2.2.0

RUN useradd -m -u 1000 executor
USER executor

CMD ["/bin/bash"]
```

---

## React Considerations

### React vs React Sandbox

| Aspect | React Image | React Sandbox |
|--------|-------------|---------------|
| **Purpose** | Component testing with Jest/React Testing Library | DOM/Browser rendering simulation |
| **Base** | Node.js 20 + React + test tools | Headless Chrome/Playwright + DOM |
| **Isolation Level** | Standard (no network) | Strict (timeout + resource limits) |
| **Use Case** | Unit/integration tests | E2E or visual regression |
| **Size** | ~1GB | ~1.5GB (headless browser) |

### Recommended Approach for React

**Option 1: Jest Tests (Recommended for Now)**
```dockerfile
# Dockerfile.executor.react
FROM node:20-slim

WORKDIR /workspace

RUN npm install -g --silent \
    jest@29.7.0 \
    react@18 \
    @testing-library/react@14

RUN useradd -m -u 1000 executor
USER executor

CMD ["/bin/bash"]
```

**Option 2: Headless Browser (Future)**
```dockerfile
# Dockerfile.executor.react-sandbox
FROM mcr.microsoft.com/playwright:v1.40.1-jammy

WORKDIR /workspace

RUN npm install -g --silent \
    jest@29.7.0 \
    playwright@1.40.1

RUN useradd -m -u 1000 executor
USER executor

CMD ["/bin/bash"]
```

---

## Migration Path

### Step 1: Document Current State
- Update architecture.md to reflect Option A
- Clarify controller vs. executor roles

### Step 2: Refactor Existing
- Rename root Dockerfile → Dockerfile.api
- Rename src/docker/python/Dockerfile → Dockerfile.executor.python
- Rename src/docker/javascript/Dockerfile → Dockerfile.executor.javascript
- Update docker-compose.yml

### Step 3: Add React
- Create Dockerfile.executor.react (Jest-based)
- Create Dockerfile.executor.react-sandbox (Playwright-based, optional)

### Step 4: Update Executor Code
- Verify DockerExecutor pulls correct image names
- Add React executor class
- Register in executor factory

### Step 5: Test & Validate
- Test all 4 executor types
- Verify isolation and security
- Update documentation

---

## Summary

| Architecture | Size | Startup | Scalability | Maintenance | Recommendation |
|--------------|------|---------|-------------|-------------|-----------------|
| **Option A** | ~500MB each | Fast | ✅ Excellent | ✅ Easy | **USE THIS** |
| **Option B** | ~2-3GB | Slow | ❌ Poor | ⚠️ Hard | Dev only |
| **Option C** | ~1.5GB | Medium | ⚠️ Moderate | ⚠️ Medium | Alternative |

**Recommendation: Implement Option A with planned React support.**

---

[← Back to Scope Matrix](01_scope-matrix.md)
