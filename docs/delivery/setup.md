# Setup Guide - Local Code Execution Engine

## Quick Start (Docker)

The fastest way to get the executor running is with Docker Compose.

### Prerequisites

- **Docker Desktop** (Mac/Windows) or **Docker + Docker Compose** (Linux)
- **Git** (to clone the repository)

### Installation & Startup

```bash
# 1. Clone the repository
git clone <repository-url>
cd code_execution_engine

# 2. Start the executor service
docker compose up

# 3. Verify it's running
curl http://localhost:7999/health
```

**Expected output:**
```json
{
    "status": "running"
}
```

That's it! The executor is now ready to accept code submissions.

---

## Manual Setup (Local Python)

If you prefer to run without Docker, you can set up locally.

### Prerequisites

- Python 3.11+
- Docker (still required for isolated code execution)
- pip

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd code_execution_engine

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the executor
python main.py
```

The server will start on `http://localhost:7999`

---

## How to Use

### 1. Health Check

Verify the executor is running:

```bash
curl http://localhost:7999/health
```

### 2. Execute Python Code

```bash
curl -X POST http://localhost:7999/execute \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "exerciseId": "python_001",
    "code": "def add(a, b):\n    return a + b"
  }'
```

### 3. Execute JavaScript Code

```bash
curl -X POST http://localhost:7999/execute \
  -H "Content-Type: application/json" \
  -d '{
    "language": "javascript",
    "exerciseId": "js_001",
    "code": "function add(a, b) { return a + b; }"
  }'
```

---

## API Reference

### Health Check

```
GET /health
```

**Response (200):**
```json
{
    "status": "running"
}
```

---

### Execute Code

```
POST /execute
```

**Request Body:**
```json
{
    "language": "python|javascript",
    "exerciseId": "unique_exercise_id",
    "code": "source code to execute",
    "timeout": 5  // optional, default 5 seconds
}
```

**Response (200 - Success):**
```json
{
    "passed": true,
    "totalTests": 3,
    "passedTests": 3,
    "failedTests": 0,
    "executionTime": 0.42,
    "memory": 22,
    "stdout": "test output here",
    "stderr": "",
    "tests": [
        {
            "name": "test_case_1",
            "status": "Passed"
        },
        {
            "name": "test_case_2",
            "status": "Passed"
        },
        {
            "name": "test_case_3",
            "status": "Passed"
        }
    ]
}
```

**Response (200 - Failure):**
```json
{
    "passed": false,
    "totalTests": 3,
    "passedTests": 2,
    "failedTests": 1,
    "executionTime": 0.38,
    "memory": 20,
    "stdout": "test output here",
    "stderr": "error details",
    "tests": [
        {
            "name": "test_case_1",
            "status": "Passed"
        },
        {
            "name": "test_case_2",
            "status": "Failed",
            "expected": "5",
            "actual": "4",
            "error": "AssertionError"
        },
        {
            "name": "test_case_3",
            "status": "Passed"
        }
    ]
}
```

**Response (422 - Validation Error):**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "language"],
            "msg": "Field required",
            "input": {}
        }
    ]
}
```

---

## Configuration

### Environment Variables

You can customize behavior with environment variables:

```bash
# Log level (debug, info, warning, error)
LOG_LEVEL=info

# Execution timeout (seconds)
EXECUTION_TIMEOUT=5

# Container memory limit (MB)
CONTAINER_MEMORY_MB=512

# Container CPU limit (0.5 = 50% of one CPU)
CONTAINER_CPU_LIMIT=0.5
```

**Docker Compose example:**
```yaml
environment:
  - LOG_LEVEL=debug
  - EXECUTION_TIMEOUT=10
  - CONTAINER_MEMORY_MB=1024
```

---

## Docker Compose Commands

### Start the executor (foreground)
```bash
docker compose up
```

### Start the executor (background)
```bash
docker compose up -d
```

### View logs
```bash
docker compose logs -f executor
```

### Stop the executor
```bash
docker compose down
```

### Rebuild images
```bash
docker compose up --build
```

### Clean up volumes
```bash
docker compose down -v
```

---

## Troubleshooting

### Port Already in Use

If port 7999 is already in use:

```bash
# Find process using port 7999
lsof -i :7999

# Kill the process (macOS/Linux)
kill -9 <PID>

# Or change the port in docker-compose.yml
# Change: ports: - "7999:7999"
# To:     ports: - "8000:7999"
```

### Docker Daemon Not Running

```bash
# On macOS, start Docker Desktop or:
open -a Docker

# On Linux:
sudo systemctl start docker
```

### Permission Denied Errors

```bash
# On Linux, add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Log out and log back in
```

### Health Check Failing

```bash
# View executor logs
docker compose logs executor

# Verify service is responding
docker compose exec executor curl http://localhost:7999/health
```

---

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/

# Lint code
pylint app/
```

---

## Performance Notes

### Typical Execution Times

- **Python startup:** ~500ms
- **Python execution:** ~0.2-0.5s
- **JavaScript startup:** ~300ms
- **JavaScript execution:** ~0.2-0.5s
- **API response:** <3s total

### Resource Limits

- **Memory per container:** 512 MB (configurable)
- **CPU per container:** 50% of one CPU (configurable)
- **Execution timeout:** 5 seconds (configurable)

---

## Security Notes

1. **Isolation:** All code executes in disposable Docker containers
2. **Network:** Containers have no network access
3. **Filesystem:** Containers have no access to host filesystem
4. **Resource Limits:** Memory and CPU are limited
5. **Cleanup:** All temporary files are deleted after execution
6. **Logging:** Source code is never stored permanently

---

## Next Steps

1. **Verify Installation:** Run `curl http://localhost:7999/health`
2. **Test Execution:** Try the example requests in [API Reference](#api-reference)
3. **Add Exercises:** Create your first exercise with test cases
4. **Integrate:** Connect the Learning Platform to `http://localhost:7999`

For detailed architecture information, see [Scope Matrix](01_scope-matrix.md).

---

[← Back to Scope Matrix](01_scope-matrix.md)
