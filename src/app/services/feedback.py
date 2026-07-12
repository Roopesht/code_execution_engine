"""AI Feedback Service - Calls LLM service for code feedback"""

import httpx
import os
import time
from datetime import datetime
from typing import List
from ..models.feedback import FeedbackRequest, FeedbackResponse, TokenUsage, FailedTest
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Level-specific guidance templates
LEVEL_GUIDANCE = {
    "beginner": "Explain in simple terms a beginner can understand. Use analogies. Avoid jargon.",
    "intermediate": "Assume the student knows basics. Be concise and technical. Provide relevant examples.",
    "advanced": "Assume deep knowledge. Get to the point. Suggest advanced techniques and optimizations.",
}

# Generic system prompt
GENERIC_SYSTEM_PROMPT = """You are a helpful coding assistant and educator.
Your task is to answer questions and provide guidance on programming topics.

Guidelines:
- Provide clear, helpful explanations
- Use examples when helpful
- Focus on teaching and learning
- Suggest best practices when relevant"""

# Language-specific system prompts for test feedback
SYSTEM_PROMPTS = {
    "python": """You are an experienced Python code reviewer and educator.
Your task is to provide constructive feedback on student code that has failed tests.

Guidelines:
- Never reveal the correct solution directly
- Only provide hints and guidance to help the student learn
- Explain mistakes clearly with examples
- Praise correct approaches when applicable
- Keep feedback concise (80-150 words)
- Focus on why the tests are failing, not what the solution is
- Point out logical errors, not just syntax issues
- Suggest debugging strategies when appropriate""",

    "javascript": """You are an experienced JavaScript code reviewer and educator.
Your task is to provide constructive feedback on student code that has failed tests.

Guidelines:
- Never reveal the correct solution directly
- Only provide hints and guidance to help the student learn
- Explain mistakes clearly with examples
- Praise correct approaches when applicable
- Keep feedback concise (80-150 words)
- Focus on why the tests are failing, not what the solution is
- Mention JavaScript best practices when relevant
- Point out async/promise issues if applicable
- Suggest debugging strategies when appropriate""",

    "react": """You are an experienced React component reviewer and educator.
Your task is to provide constructive feedback on student React code that has failed tests.

Guidelines:
- Never reveal the correct solution directly
- Only provide hints and guidance to help the student learn
- Explain mistakes clearly with examples
- Praise correct approaches when applicable
- Keep feedback concise (80-150 words)
- Focus on why the tests are failing, not what the solution is
- Comment on component patterns and lifecycle hooks
- Mention React best practices (hooks, state management, etc.)
- Point out common React pitfalls (missing dependencies, prop drilling, etc.)
- Suggest debugging strategies when appropriate""",
}


def build_prompt(
    language: str,
    code: str,
    failed_tests: List[FailedTest],
    compiler_errors: str = None,
    static_analysis: List[str] = None,
    problem_description: str = None,
    hints: List[str] = None
) -> str:
    """Build user prompt for LLM feedback request"""

    prompt_parts = []

    if problem_description:
        prompt_parts.append(f"Problem: {problem_description}")

    prompt_parts.append("Student Code:")
    prompt_parts.append(code)
    prompt_parts.append("")

    prompt_parts.append("Failed Tests:")
    for test in failed_tests:
        prompt_parts.append(f"- {test.name}:")
        prompt_parts.append(f"  Error: {test.error}")
        if test.output:
            prompt_parts.append(f"  Output: {test.output}")

    if compiler_errors:
        prompt_parts.append("")
        prompt_parts.append("Compiler/Syntax Errors:")
        prompt_parts.append(compiler_errors)

    if static_analysis:
        prompt_parts.append("")
        prompt_parts.append("Code Quality Issues:")
        for issue in static_analysis:
            prompt_parts.append(f"- {issue}")

    if hints:
        prompt_parts.append("")
        prompt_parts.append("Previous Hints Provided:")
        for hint in hints:
            prompt_parts.append(f"- {hint}")

    prompt_parts.append("")
    prompt_parts.append("Please review the code and provide feedback on why the tests are failing and how to fix the issues.")

    return "\n".join(prompt_parts)


async def get_generic_feedback(
    prompt: str,
    language: str = None,
    level: str = "intermediate",
    context: str = None,
    max_tokens_override: int = None,
    temperature_override: float = None,
) -> dict:
    """Call LLM service for generic feedback (ChatGPT-style)"""

    # Configuration
    llm_url = os.getenv("LLM_SERVICE_URL", "http://llm-server:8001")
    timeout = int(os.getenv("LLM_SERVICE_TIMEOUT", 30))
    model = os.getenv("LLM_MODEL", "qwen2.5-coder-0.5b")
    max_tokens = max_tokens_override or int(os.getenv("LLM_MAX_TOKENS", 150))
    temperature = temperature_override or float(os.getenv("LLM_TEMPERATURE", 0.7))
    top_p = float(os.getenv("LLM_TOP_P", 0.9))

    # Build system prompt with level guidance
    level_hint = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["intermediate"])
    system_prompt = f"{GENERIC_SYSTEM_PROMPT}\n\nAdapt your answer to this level: {level_hint}"

    if language:
        system_prompt += f"\nContext: {language} programming"

    # Build user prompt
    user_prompt = prompt
    if context:
        user_prompt = f"{context}\n\n{prompt}"

    logger.info({
        "event": "generic_feedback_requested",
        "level": level,
        "language": language,
        "prompt_length": len(user_prompt),
    })

    # Prepare LLM payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
    }

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            llm_endpoint = f"{llm_url}/v1/chat/completions"

            response = await client.post(llm_endpoint, json=payload)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                logger.error({
                    "event": "llm_error",
                    "status_code": response.status_code,
                    "response": response.text[:500],
                    "latency_ms": latency_ms,
                })

                if response.status_code == 503 or response.status_code == 504:
                    raise LLMUnavailableError(
                        f"LLM service returned {response.status_code}: {response.text[:100]}"
                    )
                else:
                    raise LLMError(
                        f"LLM generation failed: {response.text[:200]}"
                    )

            llm_response = response.json()
            response_text = llm_response["choices"][0]["message"]["content"]
            usage = llm_response.get("usage", {})

            logger.info({
                "event": "generic_feedback_generated",
                "latency_ms": latency_ms,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "response_length": len(response_text),
            })

            return {
                "response": response_text,
                "model": model,
                "tokens": {
                    "prompt": usage.get("prompt_tokens", 0),
                    "completion": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                },
                "latency_ms": latency_ms,
            }

    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000
        logger.error({
            "event": "llm_timeout",
            "timeout": timeout,
            "latency_ms": latency_ms,
        })
        raise LLMTimeoutError(f"LLM request timed out after {timeout} seconds")

    except httpx.ConnectError as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error({
            "event": "llm_connection_error",
            "error": str(e),
            "latency_ms": latency_ms,
        })
        raise LLMUnavailableError(
            f"Could not connect to LLM service at {llm_url}"
        )


async def get_llm_feedback(
    request: FeedbackRequest,
) -> FeedbackResponse:
    """Call LLM service and get feedback"""

    # Configuration
    llm_url = os.getenv("LLM_SERVICE_URL", "http://llm-server:8001")
    timeout = int(os.getenv("LLM_SERVICE_TIMEOUT", 30))
    model = os.getenv("LLM_MODEL", "qwen2.5-coder-0.5b")
    temperature = float(os.getenv("LLM_TEMPERATURE", 0.2))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", 150))
    top_p = float(os.getenv("LLM_TOP_P", 0.9))

    # Build prompt
    user_prompt = build_prompt(
        language=request.language,
        code=request.studentCode,
        failed_tests=request.failedTests,
        compiler_errors=request.compilerErrors,
        static_analysis=request.staticAnalysis,
        problem_description=request.problemDescription,
        hints=request.hints
    )

    # Log request
    logger.info({
        "event": "feedback_requested",
        "language": request.language,
        "exerciseId": request.exerciseId,
        "num_failed_tests": len(request.failedTests),
        "prompt_length": len(user_prompt),
    })

    # Prepare LLM payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPTS.get(request.language, SYSTEM_PROMPTS["python"])
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
    }

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try LLM call
            llm_endpoint = f"{llm_url}/v1/chat/completions"

            logger.info({
                "event": "llm_call_starting",
                "llm_url": llm_endpoint,
                "timeout": timeout,
                "model": model,
            })

            response = await client.post(llm_endpoint, json=payload)

            latency_ms = (time.time() - start_time) * 1000

            # Handle non-200 responses
            if response.status_code != 200:
                logger.error({
                    "event": "llm_error",
                    "status_code": response.status_code,
                    "response": response.text[:500],
                    "latency_ms": latency_ms,
                })

                if response.status_code == 503 or response.status_code == 504:
                    raise LLMUnavailableError(
                        f"LLM service returned {response.status_code}: {response.text[:100]}"
                    )
                else:
                    raise LLMError(
                        f"LLM generation failed: {response.text[:200]}"
                    )

            llm_response = response.json()

            # Parse response
            feedback_text = llm_response["choices"][0]["message"]["content"]
            usage = llm_response.get("usage", {})

            logger.info({
                "event": "feedback_generated",
                "latency_ms": latency_ms,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "feedback_length": len(feedback_text),
            })

            return FeedbackResponse(
                status="success",
                feedback=feedback_text,
                model=model,
                tokens=TokenUsage(
                    prompt=usage.get("prompt_tokens", 0),
                    completion=usage.get("completion_tokens", 0),
                    total=usage.get("total_tokens", 0)
                ),
                latency_ms=latency_ms,
                generatedAt=datetime.utcnow()
            )

    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000
        logger.error({
            "event": "llm_timeout",
            "timeout": timeout,
            "latency_ms": latency_ms,
        })
        raise LLMTimeoutError(f"LLM request timed out after {timeout} seconds")

    except httpx.ConnectError as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error({
            "event": "llm_connection_error",
            "error": str(e),
            "latency_ms": latency_ms,
        })
        raise LLMUnavailableError(
            f"Could not connect to LLM service at {llm_url}"
        )


# Custom Exceptions

class FeedbackError(Exception):
    """Base feedback error"""
    def __init__(self, message: str, code: str = "FEEDBACK_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class LLMError(FeedbackError):
    """LLM generation failed"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "LLM_ERROR", details)


class LLMUnavailableError(FeedbackError):
    """LLM service unavailable"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "LLM_UNAVAILABLE", details)


class LLMTimeoutError(FeedbackError):
    """LLM request timeout"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "LLM_TIMEOUT", details)
