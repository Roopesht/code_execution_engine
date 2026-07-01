# Input/Output Specification - Local Code Execution Engine

## Overview

This document specifies the complete input and output formats for the code execution system, including data types, constraints, and examples.

---

## System Flow

```
INPUT (HTTP POST)
    ├─ Program Code (user submission)
    ├─ Test Code (test file)
    ├─ Language Specification
    └─ Exercise Metadata
        │
        ▼
    EXECUTION ENGINE
        ├─ Write Program & Tests to Workspace
        ├─ Execute in Docker Container
        ├─ Run Test Framework (pytest/jest)
        ├─ Capture Results & Metrics
        │
        ▼
OUTPUT (HTTP Response)
    ├─ Execution Status
    ├─ Test Results
    ├─ Metrics
    └─ Error Information
```

---

## INPUT SPECIFICATION

### 1. Request Envelope

**Endpoint:** `POST /execute`

**Content-Type:** `application/json`

**Request Body Schema:**

```json
{
    "language": "string (required)",
    "exerciseId": "string (required)",
    "code": "string (required)",
    "tests": "string (required)",
    "timeout": "integer (optional, default: 5)"
}
```

---

### 2. Input Fields

#### 2.1 Language

**Field:** `language`

**Type:** `string`

**Required:** Yes

**Allowed Values:**
- `python`
- `javascript`

**Constraints:**
- Case-sensitive
- Must match exactly
- Future: `java`, `cpp`, `go`, `rust`

**Example:**
```json
{
    "language": "python"
}
```

**Error:** Invalid language returns 422 with validation error

---

#### 2.2 Exercise ID

**Field:** `exerciseId`

**Type:** `string`

**Required:** Yes

**Format:** `[a-z0-9_]+`

**Constraints:**
- Alphanumeric and underscores only
- 1-255 characters
- Unique identifier for exercise/problem
- Used to locate hidden test files

**Example:**
```json
{
    "exerciseId": "python_lists_001"
}
```

**Purpose:**
- Maps to test directory: `tests/exercises/{exerciseId}/`
- Used in logging for traceability
- Helps organize test fixtures by problem

---

#### 2.3 Source Code

**Field:** `code`

**Type:** `string`

**Required:** Yes

**Constraints:**
- No size limit (practical: < 1MB)
- UTF-8 encoding
- Any valid source code syntax (may contain errors)
- Not sanitized (intentional for realistic testing)
- Never stored persistently

**Example - Python:**
```json
{
    "code": "def add(a, b):\n    return a + b"
}
```

**Example - JavaScript:**
```json
{
    "code": "function multiply(a, b) { return a * b; }"
}
```

**Purpose:**
- Student/user submission
- Written to temporary workspace as `user_code.{ext}`
- Available during test execution

---

#### 2.4 Test Code

**Field:** `tests`

**Type:** `string`

**Required:** Yes

**Constraints:**
- Complete test file code
- Language-specific (pytest for Python, jest for JavaScript)
- UTF-8 encoding
- No size limit (practical: < 1MB)
- Must be valid test code syntax

**Example - Python:**
```json
{
    "tests": "import pytest\nfrom user_code import remove_duplicates\n\ndef test_simple_list():\n    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]\n\ndef test_with_duplicates():\n    assert remove_duplicates([1, 1, 2, 2]) == [1, 2]"
}
```

**Example - JavaScript:**
```json
{
    "tests": "const { multiply } = require('../user_code');\n\ndescribe('multiply', () => {\n    test('multiplies positive numbers', () => {\n        expect(multiply(3, 4)).toBe(12);\n    });\n    test('handles zero', () => {\n        expect(multiply(5, 0)).toBe(0);\n    });\n});"
}
```

**Purpose:**
- Complete test suite provided by content team/learning platform
- Written to workspace as `test_solution.py` (Python) or `solution.test.js` (JavaScript)
- Executed against user code
- Never visible to students before submission

---

#### 2.5 Timeout (Optional)

**Field:** `timeout`

**Type:** `integer`

**Required:** No

**Default:** `5` seconds

**Constraints:**
- Positive integer
- Range: 1-30 seconds
- Cannot be overridden to bypass limits
- System enforces absolute maximum

**Example:**
```json
{
    "timeout": 10
}
```

**Purpose:**
- Prevents infinite loops
- Controls resource consumption
- Per-execution limit

---

### 3. Workspace Structure

**During Execution:**

The executor creates a temporary workspace and writes the submitted code and tests:

```
/tmp/executor_<uuid>/
├── user_code.py              # User's submitted code (Python)
└── test_solution.py          # Test code from request body (Python)
```

**OR for JavaScript:**

```
/tmp/executor_<uuid>/
├── user_code.js              # User's submitted code (JavaScript)
└── solution.test.js          # Test code from request body (JavaScript)
```

**Execution Flow:**

1. **Write Files**
   - User code → `user_code.py` or `user_code.js`
   - Test code → `test_solution.py` or `solution.test.js`

2. **Mount in Docker**
   - Entire workspace mounted as `/workspace/` in container

3. **Run Tests**
   - Python: `pytest /workspace/test_solution.py -v --tb=short`
   - JavaScript: `jest /workspace/solution.test.js --json`

4. **Parse Results**
   - Capture all test results
   - Extract pass/fail counts
   - Collect output and errors

5. **Cleanup**
   - Delete entire workspace directory
   - Stop and remove Docker container

---

### 4. Complete Input Example

**HTTP Request:**
```bash
curl -X POST http://localhost:7999/execute \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "exerciseId": "python_lists_001",
    "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
    "tests": "import pytest\nfrom user_code import remove_duplicates\n\ndef test_simple_list():\n    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]\n\ndef test_with_duplicates():\n    assert remove_duplicates([1, 1, 2, 2]) == [1, 2]\n\ndef test_preserves_order():\n    assert remove_duplicates([3, 1, 2, 1]) == [3, 1, 2]\n\ndef test_empty_list():\n    assert remove_duplicates([]) == []",
    "timeout": 5
  }'
```

---

## OUTPUT SPECIFICATION

### 1. Response Envelope

**HTTP Status:** `200 OK` (regardless of execution success/failure)

**Content-Type:** `application/json`

**Response Body Schema:**

```json
{
    "passed": "boolean",
    "totalTests": "integer",
    "passedTests": "integer",
    "failedTests": "integer",
    "executionTime": "float",
    "memory": "integer",
    "stdout": "string",
    "stderr": "string",
    "tests": "array<TestResult>",
    "error": "object (optional)"
}
```

---

### 2. Output Fields

#### 2.1 Execution Status

**Field:** `passed`

**Type:** `boolean`

**Meaning:**
- `true`: All tests passed
- `false`: One or more tests failed, or execution error occurred

**Example:**
```json
{
    "passed": true
}
```

---

#### 2.2 Test Counts

**Fields:**
- `totalTests`: Total number of tests
- `passedTests`: Number of tests that passed
- `failedTests`: Number of tests that failed

**Type:** `integer`

**Constraints:**
- `passedTests + failedTests = totalTests`
- Non-negative integers
- `0` if no tests found (syntax error, import error)

**Example:**
```json
{
    "totalTests": 4,
    "passedTests": 3,
    "failedTests": 1
}
```

**Special Cases:**
- No tests found: `totalTests: 0`, `passedTests: 0`, `failedTests: 0`
- Syntax error: Same as above

---

#### 2.3 Execution Metrics

**Field:** `executionTime`

**Type:** `float`

**Unit:** Seconds

**Precision:** 2 decimal places

**Includes:**
- Code compilation time (for compiled languages)
- Test execution time
- Output collection time

**Excludes:**
- Container startup time
- Network latency

**Constraints:**
- Non-negative
- Typically < 5 seconds
- Maximum = timeout value

**Example:**
```json
{
    "executionTime": 0.42
}
```

---

**Field:** `memory`

**Type:** `integer`

**Unit:** Megabytes (MB)

**Meaning:** Peak memory usage during execution

**Constraints:**
- Non-negative integer
- Typically < 512 MB
- Maximum = container limit (512 MB default)

**Example:**
```json
{
    "memory": 18
}
```

---

#### 2.4 Standard Output & Error

**Field:** `stdout`

**Type:** `string`

**Content:**
- All output written to standard output
- Test runner output (pytest, jest)
- Print statements from user code

**Constraints:**
- UTF-8 encoded
- Maximum 64 KB
- Truncated if exceeds limit
- Empty string if no output

**Example:**
```json
{
    "stdout": "test_add_positive PASSED\ntest_add_negative PASSED\n"
}
```

---

**Field:** `stderr`

**Type:** `string`

**Content:**
- All output written to standard error
- Error messages and stack traces
- Deprecation warnings
- Runtime errors

**Constraints:**
- UTF-8 encoded
- Maximum 64 KB
- Truncated if exceeds limit
- Empty string if no errors

**Example:**
```json
{
    "stderr": "ZeroDivisionError: division by zero\n  File \"/workspace/user_code.py\", line 2, in divide\n    return a / b\n"
}
```

---

#### 2.5 Individual Test Results

**Field:** `tests`

**Type:** `array<TestResult>`

**TestResult Schema:**

```json
{
    "name": "string",
    "status": "Passed|Failed",
    "expected": "string (optional)",
    "actual": "string (optional)",
    "error": "string (optional)",
    "stackTrace": "string (optional)"
}
```

**TestResult Fields:**

**name:**
- Test function name or description
- Example: `test_add_positive`
- String, non-empty

**status:**
- `Passed`: Test assertion succeeded
- `Failed`: Test assertion failed or error occurred

**expected:** (optional)
- What the test expected
- Only present if assertion failed
- Example: `"[1, 2, 3]"`

**actual:** (optional)
- What was actually returned
- Only present if assertion failed
- Example: `"[1, 2]"`

**error:** (optional)
- Exception type and message
- Only present if error occurred
- Example: `"AssertionError"`

**stackTrace:** (optional)
- Full stack trace for debugging
- Only present if error occurred
- Multi-line string

---

### 3. Error Response

**Field:** `error` (optional)

**Type:** `object`

**Present when:**
- Syntax error in user code
- Runtime error (uncaught exception)
- Timeout exceeded
- Import/module error

**Schema:**

```json
{
    "type": "string",
    "message": "string",
    "line": "integer (optional)",
    "stackTrace": "string (optional)"
}
```

**Error Types:**
- `SyntaxError`: Invalid syntax
- `RuntimeError`: Uncaught exception
- `TimeoutError`: Execution exceeded timeout
- `ImportError`: Missing module/dependency
- `IndentationError`: Invalid indentation (Python)

**Example:**

```json
{
    "error": {
        "type": "SyntaxError",
        "message": "unexpected EOF while parsing",
        "line": 1,
        "stackTrace": "..."
    }
}
```

---

### 4. Complete Output Examples

#### 4.1 Successful Execution (All Tests Pass)

```json
{
    "passed": true,
    "totalTests": 4,
    "passedTests": 4,
    "failedTests": 0,
    "executionTime": 0.42,
    "memory": 18,
    "stdout": "test_simple_list PASSED\ntest_with_duplicates PASSED\ntest_preserves_order PASSED\ntest_empty_list PASSED\n",
    "stderr": "",
    "tests": [
        {
            "name": "test_simple_list",
            "status": "Passed"
        },
        {
            "name": "test_with_duplicates",
            "status": "Passed"
        },
        {
            "name": "test_preserves_order",
            "status": "Passed"
        },
        {
            "name": "test_empty_list",
            "status": "Passed"
        }
    ]
}
```

---

#### 4.2 Partial Failure (Some Tests Fail)

```json
{
    "passed": false,
    "totalTests": 4,
    "passedTests": 3,
    "failedTests": 1,
    "executionTime": 0.38,
    "memory": 20,
    "stdout": "test_simple_list PASSED\ntest_with_duplicates PASSED\ntest_preserves_order FAILED\ntest_empty_list PASSED\n",
    "stderr": "AssertionError: Lists are not equal\n",
    "tests": [
        {
            "name": "test_simple_list",
            "status": "Passed"
        },
        {
            "name": "test_with_duplicates",
            "status": "Passed"
        },
        {
            "name": "test_preserves_order",
            "status": "Failed",
            "expected": "[3, 1, 2]",
            "actual": "[1, 2, 3]",
            "error": "AssertionError"
        },
        {
            "name": "test_empty_list",
            "status": "Passed"
        }
    ]
}
```

---

#### 4.3 Syntax Error

```json
{
    "passed": false,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "executionTime": 0.15,
    "memory": 12,
    "stdout": "",
    "stderr": "SyntaxError: unexpected EOF while parsing",
    "tests": [],
    "error": {
        "type": "SyntaxError",
        "message": "unexpected EOF while parsing",
        "line": 1
    }
}
```

---

#### 4.4 Runtime Error

```json
{
    "passed": false,
    "totalTests": 1,
    "passedTests": 0,
    "failedTests": 1,
    "executionTime": 0.32,
    "memory": 18,
    "stdout": "",
    "stderr": "ZeroDivisionError: division by zero\n  File \"/workspace/user_code.py\", line 2, in divide\n    return a / b\n",
    "tests": [
        {
            "name": "test_divide_zero",
            "status": "Failed",
            "error": "ZeroDivisionError: division by zero",
            "stackTrace": "Traceback (most recent call last):\n  File \"/workspace/test_solution.py\", line 5, in test_divide_zero\n    result = divide(10, 0)\n  File \"/workspace/user_code.py\", line 2, in divide\n    return a / b\nZeroDivisionError: division by zero"
        }
    ],
    "error": {
        "type": "RuntimeError",
        "message": "ZeroDivisionError: division by zero"
    }
}
```

---

#### 4.5 Timeout

```json
{
    "passed": false,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "executionTime": 5.0,
    "memory": 32,
    "stdout": "",
    "stderr": "Timeout: execution exceeded 5 seconds",
    "tests": [],
    "error": {
        "type": "TimeoutError",
        "message": "execution exceeded 5 seconds"
    }
}
```

---

#### 4.6 Import Error

```json
{
    "passed": false,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "executionTime": 0.18,
    "memory": 14,
    "stdout": "",
    "stderr": "ModuleNotFoundError: No module named 'numpy'",
    "tests": [],
    "error": {
        "type": "ImportError",
        "message": "No module named 'numpy'"
    }
}
```

---

## Validation Rules

### Input Validation

| Field | Required | Type | Validation | Error Code |
|-------|----------|------|-----------|-----------|
| `language` | Yes | string | Must be 'python' or 'javascript' | 422 |
| `exerciseId` | Yes | string | 1-255 chars, alphanumeric + underscore | 422 |
| `code` | Yes | string | Non-empty, UTF-8, valid syntax for language | 422 |
| `tests` | Yes | string | Non-empty, valid test code for language | 422 |
| `timeout` | No | integer | 1-30 seconds | 422 |

### Output Validation

| Field | Type | Validation | Notes |
|-------|------|-----------|-------|
| `passed` | boolean | Required | Always present |
| `totalTests` | integer | >= 0 | Required |
| `tests` | array | 0 to many | Required (may be empty) |
| `executionTime` | float | >= 0 | Required, in seconds |
| `memory` | integer | >= 0 | Required, in MB |

---

## HTTP Status Codes

| Status | Meaning | Body |
|--------|---------|------|
| **200** | Execution completed (pass or fail) | Full response object |
| **422** | Validation error (missing/invalid field) | FastAPI validation error |
| **500** | Server error (rare, should not happen) | Error message |

---

## Data Constraints Summary

| Item | Min | Max | Default |
|------|-----|-----|---------|
| Code size | 1 byte | 1 MB | - |
| Execution time | - | 30 sec | - |
| Timeout | 1 sec | 30 sec | 5 sec |
| Memory | - | 512 MB | - |
| Output (stdout/stderr) | - | 64 KB | - |
| Exercise ID length | 1 | 255 | - |
| Tests per exercise | 1 | unlimited | - |

---

## Example Request/Response Cycle

**Request:**
```bash
POST /execute HTTP/1.1
Host: localhost:7999
Content-Type: application/json

{
    "language": "python",
    "exerciseId": "python_basics_001",
    "code": "def greet(name):\n    return f'Hello, {name}!'",
    "tests": "import pytest\nfrom user_code import greet\n\ndef test_greet_name():\n    assert greet('Alice') == 'Hello, Alice!'\n\ndef test_greet_empty():\n    assert greet('') == 'Hello, !'",
    "timeout": 5
}
```

**Response:**
```bash
HTTP/1.1 200 OK
Content-Type: application/json

{
    "passed": true,
    "totalTests": 2,
    "passedTests": 2,
    "failedTests": 0,
    "executionTime": 0.35,
    "memory": 16,
    "stdout": "test_greet_name PASSED\ntest_greet_empty PASSED\n",
    "stderr": "",
    "tests": [
        {
            "name": "test_greet_name",
            "status": "Passed"
        },
        {
            "name": "test_greet_empty",
            "status": "Passed"
        }
    ]
}
```

---

[← Back to Scope Matrix](01_scope-matrix.md)
