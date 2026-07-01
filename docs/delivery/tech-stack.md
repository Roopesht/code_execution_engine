# Tech Stack - Local Code Execution Engine

## Core Runtime

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Server Runtime** | Python | 3.11+ | Modern, stable, widely used |
| **Web Framework** | FastAPI | 0.104+ | Type safety, auto OpenAPI docs, fast, easy validation |
| **ASGI Server** | Uvicorn | 0.24+ | High performance, standard ASGI server |

---

## Container Runtime

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Container Engine** | Docker | 24.0+ | Industry standard, isolation, reproducibility |
| **Orchestration** | Docker Compose | 2.20+ | Local development and simple deployment |
| **Container Communication** | Docker Socket** | - | Access to Docker daemon for executing code |

---

## Execution Environments

### Python Execution

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Python | 3.11 | Student code execution |
| **Test Framework** | pytest | 7.4.3 | Unit test execution and reporting |
| **Coverage** | pytest-cov | 4.1.0 | Code coverage measurement |
| **Timeout** | pytest-timeout | 2.2.0 | Prevent infinite loops |
| **Base Image** | python:3.11-slim | Latest | Minimal Docker image |

### JavaScript Execution

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Runtime** | Node.js | 20 | Student code execution |
| **Test Framework** | jest | 29.7.0 | Test execution and reporting |
| **Assertion Library** | chai | 4.3.10 | Advanced assertions |
| **Alternative** | mocha | 10.2.0 | Alternative test runner |
| **Base Image** | node:20-slim | Latest | Minimal Docker image |

---

## Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **Code Formatter** | black | 23.12.0 | Python code formatting |
| **Linter** | pylint | 3.0.3 | Python code quality |
| **Testing** | pytest | 7.4.3 | Python test framework |
| **Coverage** | pytest-cov | 4.1.0 | Test coverage reporting |

---

## Python Dependencies

```
fastapi==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # ASGI server
pydantic==2.5.0           # Data validation
python-multipart==0.0.6   # Form data parsing
docker==7.0.0             # Docker API client
pytest==7.4.3             # Testing framework
pytest-cov==4.1.0         # Coverage reporting
black==23.12.0            # Code formatter
pylint==3.0.3             # Code linter
```

---

## Selection Rationale

### FastAPI vs Alternatives

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| **Type Hints** | ✅ Native | ❌ No | ⚠️ Limited |
| **Auto Docs** | ✅ OpenAPI | ❌ No | ⚠️ Third-party |
| **Performance** | ✅ Excellent | ⚠️ Good | ⚠️ Good |
| **Simplicity** | ✅ Simple | ✅ Simple | ❌ Complex |
| **Extensibility** | ✅ Easy | ✅ Easy | ❌ Hard |

**Decision:** FastAPI provides the best balance of simplicity, performance, and developer experience for a lightweight API server.

### Docker vs Alternatives

| Feature | Docker | LXC | VirtualBox |
|---------|--------|-----|-----------|
| **Portability** | ✅ Excellent | ❌ Limited | ✅ Good |
| **Performance** | ✅ Native | ✅ Native | ⚠️ Overhead |
| **Setup** | ✅ Simple | ⚠️ Complex | ⚠️ Complex |
| **Isolation** | ✅ Good | ✅ Good | ✅ Excellent |
| **Industry Standard** | ✅ Yes | ❌ No | ⚠️ Legacy |

**Decision:** Docker is the industry standard for containerization with excellent isolation and ease of use.

### pytest vs unittest

| Feature | pytest | unittest |
|---------|--------|----------|
| **Syntax** | ✅ Simple | ⚠️ Verbose |
| **Fixtures** | ✅ Flexible | ⚠️ Limited |
| **Plugins** | ✅ Extensive | ❌ No |
| **Learning Curve** | ✅ Easy | ❌ Steep |

**Decision:** pytest is the de facto standard for Python testing with better ergonomics.

### jest vs mocha

| Feature | jest | mocha |
|---------|------|-------|
| **Setup** | ✅ Zero Config | ⚠️ Manual |
| **Performance** | ✅ Excellent | ✅ Good |
| **Snapshots** | ✅ Yes | ❌ No |
| **Mocking** | ✅ Built-in | ⚠️ Third-party |
| **Popularity** | ✅ Very High | ⚠️ Medium |

**Decision:** jest is the industry standard with excellent features and minimal setup.

---

## Version Strategy

- **Lock all dependency versions** in `requirements.txt`
- **Pin Docker base images** to specific versions
- **Regular security updates** but test before upgrading
- **Minor version bumps** permitted, major versions require review

---

## Compliance Requirements

- Python 3.11+ (LTS release)
- Docker 24.0+ (Latest stable)
- Node.js 20 LTS (Latest LTS)

---

[← Back to Scope Matrix](01_scope-matrix.md)
