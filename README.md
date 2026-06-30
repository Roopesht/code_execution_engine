# Local Code Execution Engine

A lightweight, cross-platform execution engine that securely executes programming exercises inside disposable Docker containers on the user's local machine.

The engine is designed to work with the **Intelligent Programming Tutor**, but can also be integrated with any application that requires secure local code execution.

---

## Features

- Fast local execution
- Docker-based isolated execution
- FastAPI HTTP API
- Python support
- JavaScript (Node.js) support
- Language-independent architecture
- Structured execution results
- Automatic cleanup
- Cross-platform (Windows, macOS, Linux)

---

## Architecture

```text
Learning Platform
        │
        │ HTTP
        ▼
Local Code Execution Engine
        │
        ▼
FastAPI Server
        │
        ▼
Language Executor
        │
        ▼
Docker Container
        │
        ▼
Execution Results
```

---

## Supported Languages

### Current

- Python
- JavaScript (Node.js)

### Planned

- Java
- C#
- C++
- Go
- Rust
- Kotlin
- TypeScript
- SQL

---

## Prerequisites

- Docker Desktop
- Python 3.11+
- Git

---

## Installation

Clone the repository.

```bash
git clone <repository-url>

cd executor
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Start the service.

```bash
docker compose up
```

The executor will start on:

```
http://localhost:7999
```

---

## Verify Installation

### Health Check

```
GET /health
```

Example response:

```json
{
    "status": "running"
}
```

---

## Execute Code

### Endpoint

```
POST /execute
```

### Example Request

```json
{
    "language": "python",
    "exerciseId": "python_lists_001",
    "code": "def add_item(lst, item):\n    lst.append(item)\n    return lst"
}
```

### Example Response

```json
{
    "passed": true,
    "totalTests": 5,
    "passedTests": 5,
    "executionTime": 0.12,
    "memory": 18,
    "tests": [
        {
            "name": "Basic Test",
            "status": "Passed"
        }
    ]
}
```

---

## Directory Structure

```text
executor/

├── app/
│   ├── api/
│   ├── executors/
│   │   ├── python/
│   │   └── javascript/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── docker/
│   ├── python/
│   └── javascript/
│
├── tests/
├── docker-compose.yml
├── requirements.txt
└── main.py
```

---

## Execution Flow

1. Receive execution request.
2. Validate the request.
3. Create a temporary workspace.
4. Write the submitted source code.
5. Copy the hidden test files.
6. Start a Docker container.
7. Execute the tests.
8. Capture execution results.
9. Destroy the Docker container.
10. Remove the temporary workspace.
11. Return a structured JSON response.

---

## Design Principles

- Local-first execution
- Stateless architecture
- Disposable execution environments
- Language-independent design
- Easy extensibility
- Minimal cloud infrastructure
- Clear separation between execution and learning

---

## Security

Each submission executes inside a fresh Docker container.

The execution environment:

- Uses a disposable container
- Has no persistent state
- Cleans up automatically after execution
- Supports CPU and memory limits
- Can disable network access

Additional security mechanisms can be introduced without changing the public API.

---

## Roadmap

- Additional programming language support
- Plugin-based language executors
- Parallel execution
- Automatic updates
- Execution profiling
- Package management
- Resource monitoring
- Performance benchmarking

---

## Related Project

This execution engine is intended to be used with the **Intelligent Programming Tutor**, which provides:

- Problem presentation
- AI tutoring
- Adaptive hints
- Personalized feedback
- Progress tracking
- Skill assessment
- Learning analytics

The Local Code Execution Engine focuses solely on secure, reliable, and extensible code execution.
