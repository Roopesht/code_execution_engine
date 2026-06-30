# Software Requirements Specification (SRS)
# Local Code Execution Engine

## 1. Objective

Develop a lightweight local code execution engine that securely executes student programs on their own computer inside disposable Docker containers. The execution engine communicates with the Learning Platform through a local HTTP API and returns structured execution results. The engine is completely independent of the learning content and can be reused by any application requiring secure local code execution.

---

# 2. Scope

The Local Code Execution Engine is responsible for:

- Receiving source code from the Learning Platform.
- Executing code inside disposable Docker containers.
- Supporting multiple programming languages.
- Running hidden validation tests.
- Returning structured execution results.
- Providing execution diagnostics.
- Managing temporary execution environments.
- Cleaning up all temporary resources after execution.

The execution engine is **not responsible** for:

- User authentication
- Student management
- Exercise management
- AI tutoring
- Progress tracking
- Course or lesson management
- Feedback generation
- Hint generation

These responsibilities belong to the Learning Platform.

---

# 3. Design Goals

The execution engine shall be:

- Lightweight
- Fast
- Stateless
- Cross-platform
- Easily installable
- Language-independent
- Easy to extend
- Secure by default
- Independent of the Learning Platform

---

# 4. Technology Stack

## HTTP Server

**FastAPI**

Reasons:

- Excellent request validation
- Automatic OpenAPI documentation
- Strong typing
- High performance
- Easy maintenance
- Better extensibility than Flask

---

## Runtime

Python 3.x

---

## Container Runtime

Docker

Every execution shall run inside a fresh disposable Docker container.

---

# 5. Supported Languages

Initial Release

- Python
- JavaScript (Node.js)

Future support shall allow additional languages without architectural changes.

Examples:

- Java
- C#
- C++
- Go
- Rust
- Kotlin
- TypeScript
- SQL

Each language should be implemented as an independent execution module.

---

# 6. Architecture

```text
Learning Platform
        │
        │ HTTP
        ▼
localhost:7999
        │
        ▼
FastAPI Executor
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

# 7. Installation

The execution engine shall be installed once on the student's computer.

Installation process:

1. Clone repository
2. Install Python dependencies
3. Pull Docker images
4. Start FastAPI service
5. Verify installation

Example

```bash
git clone <repository>

cd executor

docker compose up
```

The installer shall verify:

- Docker installed
- Docker daemon running
- Python installed
- Required Docker images available
- Port 7999 available

---

# 8. Directory Structure

```text
executor/

    app/
        api/
        services/
        executors/
            python/
            javascript/
        models/
        utils/

    docker/
        python/
        javascript/

    tests/

    docker-compose.yml

    requirements.txt

    main.py
```

Each language implementation shall be isolated from others.

---

# 9. Language Executors

Each programming language shall provide:

- Source preparation
- Test preparation
- Execution
- Output capture
- Error capture
- Cleanup

Common interface:

```text
prepare()

execute()

collect_results()

cleanup()
```

This allows future languages to be added by implementing the same interface.

---

# 10. API Endpoints

## Health Check

```
GET /health
```

Response

```json
{
    "status":"running"
}
```

---

## Execute Code

```
POST /execute
```

Example Request

```json
{
    "language":"python",
    "exerciseId":"python_lists_001",
    "code":"def add_item(lst,item): ..."
}
```

---

## Response

```json
{
    "passed":true,
    "executionTime":0.32,
    "memory":18,
    "tests":[
        {
            "name":"Basic Test",
            "status":"Passed"
        }
    ]
}
```

---

# 11. Execution Workflow

1. Receive request.
2. Validate request.
3. Create temporary workspace.
4. Write submitted source code.
5. Copy hidden test files.
6. Start Docker container.
7. Execute tests.
8. Collect results.
9. Destroy Docker container.
10. Delete temporary workspace.
11. Return structured JSON response.

---

# 12. Docker Requirements

Each execution shall:

- Start a fresh container.
- Execute exactly one submission.
- Be automatically destroyed after execution.
- Have no persistent state.
- Execute independently of previous submissions.

Docker execution should include:

- Disposable container
- No network access
- CPU limit
- Memory limit

---

# 13. Validation

The execution engine validates:

## Syntax

Examples

- SyntaxError
- IndentationError
- Missing brackets

---

## Functional Tests

Hidden unit tests.

---

## Edge Cases

Examples

- Empty input
- Null values
- Large datasets
- Boundary conditions

---

## Runtime Errors

Examples

- Division by zero
- Index out of range
- Key not found
- Infinite recursion

---

# 14. Result Format

The execution engine shall return only technical execution data.

Example

```json
{
    "passed":false,
    "totalTests":6,
    "passedTests":4,
    "failedTests":2,
    "executionTime":0.18,
    "memory":22,
    "stdout":"...",
    "stderr":"...",
    "tests":[
        {
            "name":"Edge Case",
            "status":"Failed",
            "expected":"10",
            "actual":"8",
            "error":"AssertionError"
        }
    ]
}
```

The Learning Platform is responsible for converting this information into educational feedback.

---

# 15. Logging

The executor shall log:

- Request received
- Language
- Exercise ID
- Execution duration
- Docker exit status
- Internal errors

Student source code shall not be permanently stored.

---

# 16. Performance Requirements

Typical execution:

- Startup < 1 second
- Typical execution < 2 seconds
- API response < 3 seconds

The executor shall support multiple sequential requests without requiring restart.

---

# 17. Future Enhancements

The architecture shall support:

- Additional programming languages
- Parallel execution
- Docker image caching
- Automatic executor updates
- Plugin-based language executors
- Resource monitoring
- Execution profiling
- Package management
- Custom runtime environments

---

# 18. Success Criteria

The Local Code Execution Engine will be considered successful if it:

- Executes Python and JavaScript code inside isolated Docker containers.
- Provides a stable HTTP API for the Learning Platform.
- Returns consistent, structured execution results.
- Cleans up all temporary resources after execution.
- Supports future programming languages through a modular executor architecture.
- Operates independently of the Learning Platform while remaining easy to install, maintain, and extend.
