# Input/Output Examples - Local Code Execution Engine

## Complete Request/Response Cycles

This document provides real-world examples with complete payloads showing the flow from submission through execution to results.

---

## Example 1: Simple Python Function (Success)

### Scenario
Student submits a solution to a list manipulation exercise. The code is correct and all tests pass.

### Step 1: Student Submits Code

**HTTP Request:**

```http
POST /execute HTTP/1.1
Host: localhost:7999
Content-Type: application/json

{
    "language": "python",
    "exerciseId": "python_lists_001",
    "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
    "tests": "import pytest\nfrom user_code import remove_duplicates\n\ndef test_simple_list():\n    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]\n\ndef test_with_duplicates():\n    assert remove_duplicates([1, 1, 2, 2]) == [1, 2]\n\ndef test_preserves_order():\n    assert remove_duplicates([3, 1, 2, 1]) == [3, 1, 2]\n\ndef test_empty_list():\n    assert remove_duplicates([]) == []",
    "timeout": 5
}
```

**Raw JSON (formatted):**
```json
{
    "language": "python",
    "exerciseId": "python_lists_001",
    "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
    "tests": "import pytest\nfrom user_code import remove_duplicates\n\ndef test_simple_list():\n    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]\n\ndef test_with_duplicates():\n    assert remove_duplicates([1, 1, 2, 2]) == [1, 2]\n\ndef test_preserves_order():\n    assert remove_duplicates([3, 1, 2, 1]) == [3, 1, 2]\n\ndef test_empty_list():\n    assert remove_duplicates([]) == []",
    "timeout": 5
}
```

### Step 2: Executor Processes Request

**Internal Flow:**

1. **Validation** ✓
   - Language: `python` → Valid
   - ExerciseId: `python_lists_001` → Valid
   - Code: Present and non-empty ✓
   - Timeout: 5 seconds → Valid

2. **Preparation**
   - Create temp workspace: `/tmp/executor_<uuid>/`
   - Write code to: `/workspace/user_code.py`
   - Load tests from: `tests/exercises/python_lists_001/`
   - Copy test file: `test_solution.py`

3. **Test File Content:**
   ```python
   # tests/exercises/python_lists_001/test_solution.py
   import pytest
   from user_code import remove_duplicates

   def test_simple_list():
       assert remove_duplicates([1, 2, 3]) == [1, 2, 3]

   def test_with_duplicates():
       assert remove_duplicates([1, 1, 2, 2]) == [1, 2]

   def test_preserves_order():
       assert remove_duplicates([3, 1, 2, 1]) == [3, 1, 2]

   def test_empty_list():
       assert remove_duplicates([]) == []
   ```

4. **Docker Execution**
   - Start container: `docker run python:3.11-slim`
   - Mount workspace
   - Run: `pytest test_solution.py -v --tb=short --json-report`

5. **Test Results**
   ```
   test_simple_list PASSED
   test_with_duplicates PASSED
   test_preserves_order PASSED
   test_empty_list PASSED
   ```

6. **Metrics Collected**
   - Execution time: 0.42 seconds
   - Memory used: 18 MB
   - All tests: 4
   - Passed: 4
   - Failed: 0

### Step 3: Return Response

**HTTP Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 1247

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

**Response Summary:**
```
✅ Status: PASSED
✅ Tests: 4/4 passed
⏱️  Time: 0.42s
💾 Memory: 18 MB
📝 Output: Clear test output, no errors
```

---

## Example 2: Python Function with Logic Error (Partial Failure)

### Scenario
Student submits a solution that works for most cases but fails on one edge case.

### Step 1: Student Submits Code

**HTTP Request:**

```json
{
    "language": "python",
    "exerciseId": "python_strings_002",
    "code": "def is_palindrome(s):\n    cleaned = s.lower()\n    return cleaned == cleaned[::-1]",
    "tests": "import pytest\nfrom user_code import is_palindrome\n\ndef test_simple_palindrome():\n    assert is_palindrome('racecar') == True\n\ndef test_simple_non_palindrome():\n    assert is_palindrome('hello') == False\n\ndef test_with_spaces():\n    assert is_palindrome('race car') == True\n\ndef test_with_punctuation():\n    assert is_palindrome('A man, a plan, a canal: Panama') == True",
    "timeout": 5
}
```

**Problem:** The function doesn't remove spaces/punctuation, only works for simple cases.

### Step 2: Executor Processes & Tests

**Test File:**
```python
# tests/exercises/python_strings_002/test_solution.py
import pytest
from user_code import is_palindrome

def test_simple_palindrome():
    assert is_palindrome("racecar") == True

def test_simple_non_palindrome():
    assert is_palindrome("hello") == False

def test_with_spaces():
    assert is_palindrome("race car") == True  # Expects True

def test_with_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama") == True
```

**Execution Results:**
- ✅ test_simple_palindrome: PASSED
- ✅ test_simple_non_palindrome: PASSED
- ❌ test_with_spaces: FAILED (expected True, got False)
- ❌ test_with_punctuation: FAILED (expected True, got False)

### Step 3: Return Response

**HTTP Response:**

```json
{
    "passed": false,
    "totalTests": 4,
    "passedTests": 2,
    "failedTests": 2,
    "executionTime": 0.38,
    "memory": 16,
    "stdout": "test_simple_palindrome PASSED\ntest_simple_non_palindrome PASSED\ntest_with_spaces FAILED\ntest_with_punctuation FAILED\n",
    "stderr": "AssertionError: assert False == True\n",
    "tests": [
        {
            "name": "test_simple_palindrome",
            "status": "Passed"
        },
        {
            "name": "test_simple_non_palindrome",
            "status": "Passed"
        },
        {
            "name": "test_with_spaces",
            "status": "Failed",
            "expected": "True",
            "actual": "False",
            "error": "AssertionError"
        },
        {
            "name": "test_with_punctuation",
            "status": "Failed",
            "expected": "True",
            "actual": "False",
            "error": "AssertionError"
        }
    ]
}
```

**Response Summary:**
```
❌ Status: FAILED
📊 Tests: 2/4 passed, 2 failed
⏱️  Time: 0.38s
💾 Memory: 16 MB
⚠️  Issues: Doesn't handle spaces/punctuation
```

---

## Example 3: Python Syntax Error

### Scenario
Student submits code with a syntax error (missing colon, unclosed parenthesis, etc.).

### Step 1: Student Submits Code

**HTTP Request:**

```json
{
    "language": "python",
    "exerciseId": "python_functions_001",
    "code": "def calculate(x, y\n    return x + y",
    "tests": "import pytest\nfrom user_code import calculate\n\ndef test_add():\n    assert calculate(2, 3) == 5",
    "timeout": 5
}
```

**Problem:** Missing closing parenthesis on line 1.

### Step 2: Executor Attempts to Process

**During Validation Phase:**
- Try to compile code
- Python parser fails
- Syntax error detected

### Step 3: Return Response

**HTTP Response:**

```json
{
    "passed": false,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "executionTime": 0.08,
    "memory": 10,
    "stdout": "",
    "stderr": "SyntaxError: '(' was never closed",
    "tests": [],
    "error": {
        "type": "SyntaxError",
        "message": "'(' was never closed",
        "line": 1
    }
}
```

**Response Summary:**
```
❌ Status: FAILED
🔴 Error: SyntaxError
💣 Message: '(' was never closed on line 1
⏱️  Time: 0.08s (quick failure)
💾 Memory: 10 MB
📝 No tests run (syntax error blocks execution)
```

---

## Example 4: Python Runtime Error

### Scenario
Student submits code that compiles but crashes during test execution.

### Step 1: Student Submits Code

**HTTP Request:**

```json
{
    "language": "python",
    "exerciseId": "python_division_001",
    "code": "def divide_safe(a, b):\n    return a / b",
    "tests": "import pytest\nfrom user_code import divide_safe\n\ndef test_normal_division():\n    assert divide_safe(10, 2) == 5\n\ndef test_divide_by_zero():\n    assert divide_safe(10, 0) == float('inf')",
    "timeout": 5
}
```

**Problem:** No zero-check; will crash when b=0.

### Step 2: Executor Processes & Tests

**Test File:**
```python
from user_code import divide_safe

def test_normal_division():
    assert divide_safe(10, 2) == 5

def test_divide_by_zero():
    assert divide_safe(10, 0) == float('inf')  # Expected to handle gracefully
```

**Execution:**
- ✅ test_normal_division: PASSED
- ❌ test_divide_by_zero: FAILED with ZeroDivisionError

### Step 3: Return Response

**HTTP Response:**

```json
{
    "passed": false,
    "totalTests": 2,
    "passedTests": 1,
    "failedTests": 1,
    "executionTime": 0.35,
    "memory": 14,
    "stdout": "test_normal_division PASSED\n",
    "stderr": "ZeroDivisionError: division by zero\n  File \"/workspace/test_solution.py\", line 5, in test_divide_by_zero\n    result = divide_safe(10, 0)\n  File \"/workspace/user_code.py\", line 2, in divide_safe\n    return a / b\nZeroDivisionError: division by zero\n",
    "tests": [
        {
            "name": "test_normal_division",
            "status": "Passed"
        },
        {
            "name": "test_divide_by_zero",
            "status": "Failed",
            "error": "ZeroDivisionError: division by zero",
            "stackTrace": "Traceback (most recent call last):\n  File \"/workspace/test_solution.py\", line 5, in test_divide_by_zero\n    result = divide_safe(10, 0)\n  File \"/workspace/user_code.py\", line 2, in divide_safe\n    return a / b\nZeroDivisionError: division by zero"
        }
    ],
    "error": {
        "type": "RuntimeError",
        "message": "ZeroDivisionError: division by zero"
    }
}
```

**Response Summary:**
```
❌ Status: FAILED
🔴 Error: ZeroDivisionError
💥 Runtime error in divide_safe() function
📍 Line 2: return a / b
⏱️  Time: 0.35s
💾 Memory: 14 MB
```

---

## Example 5: Python Timeout (Infinite Loop)

### Scenario
Student submits code that enters an infinite loop.

### Step 1: Student Submits Code

**HTTP Request:**

```json
{
    "language": "python",
    "exerciseId": "python_loops_001",
    "code": "def find_prime(n):\n    while True:\n        pass  # Infinite loop!",
    "tests": "import pytest\nfrom user_code import find_prime\n\ndef test_find_prime():\n    assert find_prime(10) == 7",
    "timeout": 5
}
```

### Step 2: Executor Processes

**During Execution:**
- Start container
- Run tests
- After 5 seconds (timeout), container is still running
- System terminates execution

### Step 3: Return Response

**HTTP Response:**

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

**Response Summary:**
```
❌ Status: FAILED
⏱️  Error: TimeoutError (5.0s)
💾 Memory: 32 MB
⚠️  Likely infinite loop or very slow code
```

---

## Example 6: Python Missing Dependency

### Scenario
Student submits code that imports a module not installed in the container.

### Step 1: Student Submits Code

**HTTP Request:**

```json
{
    "language": "python",
    "exerciseId": "python_numpy_001",
    "code": "import numpy as np\n\ndef process_array(arr):\n    return np.sum(arr)",
    "tests": "import pytest\nfrom user_code import process_array\n\ndef test_sum_array():\n    assert process_array([1, 2, 3]) == 6",
    "timeout": 5
}
```

**Problem:** numpy is not installed in the Python container.

### Step 2: Executor Attempts Import

**During Code Load:**
- Try to import numpy
- Module not found
- ImportError raised before tests run

### Step 3: Return Response

**HTTP Response:**

```json
{
    "passed": false,
    "totalTests": 0,
    "passedTests": 0,
    "failedTests": 0,
    "executionTime": 0.12,
    "memory": 11,
    "stdout": "",
    "stderr": "ModuleNotFoundError: No module named 'numpy'",
    "tests": [],
    "error": {
        "type": "ImportError",
        "message": "No module named 'numpy'"
    }
}
```

**Response Summary:**
```
❌ Status: FAILED
🔴 Error: ModuleNotFoundError
📦 Missing dependency: numpy
⏱️  Time: 0.12s (quick failure)
💾 Memory: 11 MB
```

---

## Comparison Table: All Outcomes

| Scenario | Status | Tests | Time | Memory | Error |
|----------|--------|-------|------|--------|-------|
| Success | ✅ Passed | 4/4 | 0.42s | 18 MB | None |
| Partial | ❌ Failed | 2/4 | 0.38s | 16 MB | AssertionError |
| Syntax | ❌ Failed | 0/0 | 0.08s | 10 MB | SyntaxError |
| Runtime | ❌ Failed | 1/2 | 0.35s | 14 MB | ZeroDivisionError |
| Timeout | ❌ Failed | 0/0 | 5.0s | 32 MB | TimeoutError |
| Import | ❌ Failed | 0/0 | 0.12s | 11 MB | ModuleNotFoundError |

---

## How to Use These Examples

### For API Consumers
1. Use the request payloads as templates for your submissions
2. Expect responses in the format shown
3. Handle different response types (success, failure, error)

### For Test Data
Copy the request payloads to test your integration:

```bash
curl -X POST http://localhost:7999/execute \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "exerciseId": "python_lists_001",
    "code": "def remove_duplicates(lst):\n    seen = set()\n    result = []\n    for item in lst:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
    "tests": "import pytest\nfrom user_code import remove_duplicates\n\ndef test_simple_list():\n    assert remove_duplicates([1, 2, 3]) == [1, 2, 3]\n\ndef test_with_duplicates():\n    assert remove_duplicates([1, 1, 2, 2]) == [1, 2]",
    "timeout": 5
  }'
```

### For Learning Platform Integration
The response structure allows you to:
1. Check `passed` field to determine overall outcome
2. Count `passedTests` vs `failedTests` for progress
3. Parse individual `tests` for detailed feedback
4. Show `error` information when execution fails
5. Display `stdout`/`stderr` for debugging
6. Track `executionTime` and `memory` for performance analysis

---

[← Back to Scope Matrix](01_scope-matrix.md)
