# Integration Guide - Local Code Execution Engine

**For:** Web apps, learning platforms, IDEs needing safe code execution

---

## What You Get

- **Safe code execution** in isolated Docker containers
- **Multi-language support** (Python, JavaScript - more coming)
- **Automatic test execution** with detailed results
- **Novice-friendly error messages** with hints
- **API-first design** for easy integration

---

## Setup

Before integrating with your website, you need to set up the execution engine on your server.

**See:** [SETUP_LOCAL_ENGINE.md](SETUP_LOCAL_ENGINE.md) for detailed setup instructions (Docker or Python).

Once set up, the engine will be running at `http://localhost:7999` (or your server address).

---

## API Reference

### Health Check

```
GET /health
```
No auth required. Returns `{"status": "running"}`.

### Execute Code

```
POST /execute
X-API-Key: your_api_key
Content-Type: application/json

{
  "language": "python",              // or "javascript"
  "exerciseId": "exercise_slug",     // alphanumeric + underscore
  "code": "def add(a, b):\n  return a + b",
  "tests": "def test_add():\n  assert add(1, 2) == 3",
  "timeout": 5                       // optional, 1-30 seconds
}
```

**Response (Success):**
```json
{
  "passed": true,
  "totalTests": 2,
  "passedTests": 2,
  "failedTests": 0,
  "executionTime": 0.234,
  "memory": 12.5,
  "stdout": "=== test session starts ===\n...",
  "stderr": "",
  "tests": [
    {
      "name": "test_add",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    },
    {
      "name": "test_multiply",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    }
  ],
  "error": null
}
```

**Response (With Failures - Human-Readable Error Details):**
```json
{
  "passed": false,
  "totalTests": 2,
  "passedTests": 1,
  "failedTests": 1,
  "executionTime": 0.456,
  "memory": 12.5,
  "stdout": "=== test session starts ===\n...",
  "stderr": "",
  "tests": [
    {
      "name": "test_add",
      "status": "Passed",
      "expected": null,
      "actual": null,
      "error": null,
      "stackTrace": null
    },
    {
      "name": "test_divide",
      "status": "Failed",
      "expected": "Infinity",
      "actual": "ZeroDivisionError",
      "error": "assert <result> == Infinity",
      "stackTrace": "where ZeroDivisionError = divide(10, 0)"
    }
  ],
  "error": null
}
```

**Note:** For failed tests, each test result includes:
- `expected` - What the test expected
- `actual` - What the code returned/error type
- `error` - The assertion that failed (human-readable)
- `stackTrace` - Additional context (e.g., which function caused the issue)

These details help novice users understand exactly what went wrong and how to fix it.

**Error Response (422):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "language"],
      "msg": "Input should be 'python' or 'javascript'"
    }
  ]
}
```

**Auth Failure (401):**
```json
{"detail": "Unauthorized"}
```

---

## Integration Examples

### JavaScript/React - Execute Code

```javascript
const executeCode = async (code, tests) => {
  const response = await fetch('http://localhost:7999/execute', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your_api_key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      language: 'python',
      exerciseId: 'my_exercise',
      code,
      tests
    })
  });
  
  const result = await response.json();
  
  if (result.passed) {
    console.log('✅ All tests passed!');
  } else {
    console.log(`❌ ${result.failedTests} test(s) failed`);
    console.log(result.error?.hint);
  }
  
  return result;
};
```

### JavaScript/React - Generic Feedback (ChatGPT-style)

```javascript
const getGenericFeedback = async (prompt, level = 'intermediate') => {
  const response = await fetch('http://localhost:7999/feedback', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your_api_key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: prompt,
      language: 'javascript',
      level: level,  // 'beginner', 'intermediate', 'advanced'
      max_tokens: 200
    })
  });
  
  const result = await response.json();
  console.log('🤖 Response:', result.response);
  return result;
};

// Usage: Answer any question
getGenericFeedback("What's the difference between let and const?", "beginner");
```

### JavaScript/React - Test-Specific Feedback

```javascript
const getTestFeedback = async (code, failedTests, exerciseId) => {
  const response = await fetch('http://localhost:7999/feedback-test', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your_api_key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      language: 'javascript',
      exerciseId: exerciseId,
      studentCode: code,
      failedTests: failedTests.map(t => ({
        name: t.name,
        error: t.error,
        output: t.output
      }))
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error(`Error (${response.status}):`, error.error);
    return null;
  }
  
  const result = await response.json();
  console.log('🤖 Feedback:', result.feedback);
  console.log(`Tokens used: ${result.tokens.total}`);
  console.log(`Response time: ${result.latency_ms}ms`);
  
  return result;
};

// Usage: When tests fail, get feedback
const result = await executeCode(studentCode, tests);
if (!result.passed) {
  const feedback = await getTestFeedback(
    studentCode,
    result.tests.filter(t => t.status === 'Failed'),
    'my_exercise'
  );
}
```

### Python - Execute Code

```python
import requests

response = requests.post(
    'http://localhost:7999/execute',
    headers={'X-API-Key': 'your_api_key'},
    json={
        'language': 'python',
        'exerciseId': 'my_exercise',
        'code': 'def add(a, b):\n  return a + b',
        'tests': 'def test_add():\n  assert add(1, 2) == 3'
    }
)

result = response.json()
print(f"Passed: {result['passed']}")
print(f"Tests: {result['passedTests']}/{result['totalTests']}")
```

### Python - Get AI Feedback

```python
import requests

# After execution, if tests failed
execution_result = requests.post(
    'http://localhost:7999/execute',
    headers={'X-API-Key': 'api_key'},
    json={'language': 'python', 'exerciseId': 'algo-sort', ...}
).json()

if not execution_result['passed']:
    # Get AI feedback on failures
    feedback_response = requests.post(
        'http://localhost:7999/feedback',
        headers={'X-API-Key': 'api_key'},
        json={
            'language': 'python',
            'exerciseId': 'algo-sort',
            'studentCode': student_code,
            'failedTests': [
                {
                    'name': t['name'],
                    'error': t['error'],
                    'output': t.get('output')
                }
                for t in execution_result['tests']
                if t['status'] == 'Failed'
            ]
        }
    )
    
    if feedback_response.status_code == 200:
        feedback = feedback_response.json()
        print(f"🤖 Feedback: {feedback['feedback']}")
        print(f"Tokens: {feedback['tokens']['total']}")
    else:
        print(f"Error: {feedback_response.json()['error']}")
```

---

## Configuration

### Environment Variables

**Required:**
- `EXECUTOR_API_KEY` - API key (min 32 chars, letters + numbers)

**CORS:**
- `CORS_ORIGINS` - Comma-separated allowed origins
  - Dev: `http://localhost:3000,http://localhost:8000`
  - Prod: `https://yourdomain.com,https://app.yourdomain.com`

**Optional:**
- `LOG_LEVEL` - INFO (default) | DEBUG
- `EXECUTION_TIMEOUT` - 1-30 seconds (default 5)
- `CONTAINER_MEMORY_MB` - Memory limit (default 512)
- `CONTAINER_CPU_LIMIT` - CPU cores (default 0.5)
- `HOST` - Bind address (default 0.0.0.0)
- `PORT` - Port (default 7999)

---

## Docker Isolation & Limits

Each execution runs in isolated container with:

| Limit | Value | Purpose |
|-------|-------|---------|
| Memory | 512 MB | Prevent runaway processes |
| CPU | 0.5 cores | Fair resource sharing |
| Timeout | 5s max | Prevent infinite loops |
| Network | Disabled | Prevent data exfiltration |
| Filesystem | Read-write `/workspace` only | Prevent host access |

---

## Security

- **API Key:** Required for all endpoints except `/health`
- **CORS:** Allowed origins configurable per environment
- **Validation:** All inputs validated (Pydantic)
- **Logging:** Code NEVER logged (only IDs, errors, metrics)
- **Headers:** Security headers on all responses

See [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) for details.

---

## AI Feedback Endpoints

**Story 6.4** provides two AI-powered feedback endpoints:

### 1. Generic Feedback - ChatGPT-Style API

Ask any question about code, debugging, concepts, etc. Responses adapt to the user's level.

```
POST /feedback
X-API-Key: your_api_key
Content-Type: application/json

{
  "prompt": "Explain what a closure is in JavaScript",
  "language": "javascript",        // optional: python, javascript, react
  "level": "beginner",             // beginner, intermediate (default), advanced
  "context": "I'm learning ES6",   // optional: additional context
  "max_tokens": 150,               // optional: 50-500 (default 150)
  "temperature": 0.7               // optional: 0-2 (default 0.7)
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "response": "A closure is a function that has access to variables from its outer scope...",
  "model": "qwen2.5-coder-0.5b",
  "tokens": {
    "prompt": 45,
    "completion": 78,
    "total": 123
  },
  "latency_ms": 850,
  "generatedAt": "2024-07-09T10:30:00Z"
}
```

**Features:**
- Works with any question or prompt
- Tailored responses for beginner/intermediate/advanced levels
- Optional language context for code-specific questions
- Adjustable creativity (temperature) and response length
- Full token usage tracking

---

### 2. Test-Specific Feedback - Failed Test Analysis

Analyzes student code that failed tests and provides targeted guidance.

```
POST /feedback-test
X-API-Key: your_api_key
Content-Type: application/json

{
  "language": "python",              // python, javascript, or react
  "exerciseId": "exercise_slug",
  "studentCode": "def add(a, b):\n  return a",
  "failedTests": [
    {
      "name": "test_add",
      "error": "AssertionError: expected 3, got 1",
      "output": "..."  // optional test output
    }
  ],
  "compilerErrors": null,            // optional
  "staticAnalysis": [                // optional
    "Missing docstring",
    "No type hints"
  ],
  "problemDescription": "Add two numbers",  // optional
  "hints": ["Check your return statement"]   // optional
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "feedback": "Your add function looks good, but I notice you're only returning `a` instead of adding both parameters. Try returning `a + b` instead.",
  "model": "qwen2.5-coder-0.5b",
  "tokens": {
    "prompt": 156,
    "completion": 45,
    "total": 201
  },
  "latency_ms": 850,
  "generatedAt": "2024-07-09T10:30:00Z"
}
```

**Features:**
- **Language-specific prompts**: Python, JavaScript, React each have tailored guidance
- **Intelligent analysis**: Examines failed tests, compiler errors, and code quality issues
- **Novice-friendly**: Provides hints without revealing solutions
- **Fast feedback**: Generated in ~500-1000ms (depends on LLM service)
- **Token tracking**: See prompt/completion token usage

### Error Responses

| Status | Code | Meaning |
|--------|------|---------|
| **400** | INVALID_REQUEST | Missing/invalid fields |
| **401** | UNAUTHORIZED | Invalid API key |
| **500** | LLM_ERROR | LLM generation failed |
| **503** | LLM_UNAVAILABLE | LLM service not running |
| **504** | LLM_TIMEOUT | LLM took too long (>30s) |

---

## Supported Languages

| Language | Execute | Feedback | Notes |
|----------|---------|----------|-------|
| Python | ✅ Ready | ✅ Ready | Full support |
| JavaScript | ✅ Ready | ✅ Ready | Full support |
| React | ❌ Planned | ✅ Ready | Feedback only (Story 3.3) |

---

## Troubleshooting

### 401 Unauthorized
- Check `X-API-Key` header matches `EXECUTOR_API_KEY`
- Verify health check works: `curl http://localhost:7999/health`

### 422 Validation Error
- Check `language` is `python` or `javascript`
- Check `exerciseId` matches `^[a-z0-9_]+$`
- Check `code` and `tests` are strings, < 1MB each

### 500 Internal Error
- Check Docker is running: `docker ps`
- Check container has Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock`
- Check logs: `docker logs <container_id>`

### CORS Errors
- Add your origin to `CORS_ORIGINS` in `.env`
- Restart container after changing `.env`

---

## Adding AI Feedback to 3rd Party Sites

### Quick Integration Checklist

For a learning platform or coding IDE that already calls `/execute`, adding AI feedback is just 3 extra lines:

1. **After code execution fails:**
   ```javascript
   const execution = await executeCode(studentCode, tests);
   if (!execution.passed) {
     const feedback = await getFeedback(studentCode, execution.tests);
   }
   ```

2. **Show feedback to student:**
   ```javascript
   console.log(feedback.feedback);  // Display AI's guidance
   ```

3. **That's it!** No LLM setup needed on your end.

### Architecture for 3rd Party Integration

```
Your Web App
    ↓
  [Execute Button]
    ↓
  POST /execute (code + tests)
    ↓
  Tests fail? → Check result.passed
    ↓
  if (!passed) POST /feedback (code + failed tests)
    ↓
  Display feedback to student
```

### Example: Add to Existing Platform

If you're already calling the executor API, this is a minimal addition:

```javascript
// You already have this:
const result = await executeCode(code, tests);

// Add this:
if (!result.passed) {
  try {
    const feedback = await fetch('http://executor:7999/feedback', {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        language: 'python',
        exerciseId: exercise.id,
        studentCode: code,
        failedTests: result.tests
          .filter(t => t.status === 'Failed')
          .map(t => ({name: t.name, error: t.error}))
      })
    }).then(r => r.json());
    
    // Display: feedback.feedback
    showToStudent(feedback.feedback);
  } catch (e) {
    console.error('Feedback unavailable:', e);
    // Graceful degradation - still show test results
  }
}
```

### What Your Users See

**Before (Test Results Only):**
```
❌ test_sort failed: expected [1,2,3], got [3,2,1]
```

**After (With AI Feedback):**
```
❌ test_sort failed: expected [1,2,3], got [3,2,1]

🤖 AI Feedback:
Your sort implementation isn't changing the array order. 
I notice you're returning `arr` directly without actually 
sorting it. Try using Python's built-in `sorted()` function 
and remember to return the result. Here's a hint: 
`return sorted(arr)` would work for this case.
```

### Performance Considerations

- **Feedback latency:** 500ms - 1500ms (LLM response time)
- **Best practice:** Load feedback asynchronously after showing test results
- **Fallback:** If feedback fails (LLM unavailable), still show execution results
- **Caching:** Future story (6.2) will add response caching

### Costs

Each feedback request uses LLM tokens:
- **Prompt tokens:** ~150-400 (depends on code size)
- **Completion tokens:** ~50-150 (feedback length)
- **Total per request:** ~200-500 tokens

### Requirements on Your End

- ✅ Call `/execute` first (you already do)
- ✅ Extract failed tests from response
- ✅ Send to `/feedback` endpoint
- ✅ Display `feedback.feedback` to user
- ✅ Handle errors gracefully (LLM might be down)

### Optional Features

**Track feedback usage:**
```javascript
analytics.track('feedback_requested', {
  language: 'python',
  exercise_id: 'algo-sort',
  tokens_used: feedback.tokens.total,
  latency_ms: feedback.latency_ms
});
```

**Show token usage to admin:**
```javascript
// For billing/monitoring
console.log(`Feedback token cost: ${feedback.tokens.total}`);
```

**Language detection:**
```javascript
// Auto-detect from exercise metadata
const language = exercise.language || 'python';
```

---

## Next Steps

1. **Deploy** using Docker or local Python
2. **Test** with curl or Postman
3. **Integrate** `/execute` first (existing flow)
4. **Add** `/feedback` endpoint (new AI feature)
5. **Display** feedback to students
6. **Monitor** via logs (JSON format, queryable)

See [SECURITY_CONFIGURATION.md](SECURITY_CONFIGURATION.md) for production setup.

---

[← Back to Scope Matrix](01_scope-matrix.md)
