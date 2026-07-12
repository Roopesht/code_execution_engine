from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


class TokenUsage(BaseModel):
    """Token usage statistics"""
    prompt: int
    completion: int
    total: int


class FailedTest(BaseModel):
    """Represents a failed test"""
    name: str = Field(min_length=1, max_length=255)
    error: str = Field(min_length=1, max_length=1000)
    output: Optional[str] = Field(default=None, max_length=1000)


# Generic Feedback (ChatGPT-style)

class GenericFeedbackRequest(BaseModel):
    """Generic feedback request - like ChatGPT API"""
    prompt: str = Field(min_length=1, max_length=5000, description="Any question or text")
    language: Optional[Literal["python", "javascript", "react"]] = Field(
        default=None, description="Programming language (optional)"
    )
    level: Optional[Literal["beginner", "intermediate", "advanced"]] = Field(
        default="intermediate", description="Explanation level for user"
    )
    context: Optional[str] = Field(default=None, max_length=1000, description="Additional context")
    max_tokens: Optional[int] = Field(default=150, ge=50, le=500, description="Max response tokens")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Creativity level")


class GenericFeedbackResponse(BaseModel):
    """Generic feedback response"""
    status: Literal["success", "error"]
    response: str = Field(description="AI response to the prompt")
    model: str = Field(default="qwen2.5-coder-0.5b")
    tokens: TokenUsage
    latency_ms: float
    generatedAt: datetime


# Test-Specific Feedback

class FeedbackRequest(BaseModel):
    """Request for AI feedback on failed code"""
    language: Literal["python", "javascript", "react"] = Field(description="Programming language")
    exerciseId: str = Field(min_length=1, max_length=255, pattern="^[a-z0-9_]+$")
    studentCode: str = Field(min_length=1, max_length=2000, description="Student's submitted code")
    failedTests: List[FailedTest] = Field(min_items=1, max_items=5, description="Failed tests (1-5)")
    compilerErrors: Optional[str] = Field(default=None, max_length=1000, description="Syntax/compilation errors")
    staticAnalysis: Optional[List[str]] = Field(default=None, max_items=10, description="Code quality issues")
    problemDescription: Optional[str] = Field(default=None, max_length=500, description="Original problem statement")
    hints: Optional[List[str]] = Field(default=None, max_items=5, description="Hints already provided")


class FeedbackResponse(BaseModel):
    """Response with AI feedback"""
    status: Literal["success", "error"]
    feedback: str = Field(description="AI-generated feedback on failed code")
    model: str = Field(default="qwen2.5-coder-0.5b")
    tokens: TokenUsage
    latency_ms: float = Field(description="Request latency in milliseconds")
    generatedAt: datetime


class ErrorDetail(BaseModel):
    """Error response details"""
    field: Optional[str] = None
    reason: Optional[str] = None
    limit: Optional[int] = None
    actual: Optional[int] = None
    supported: Optional[List[str]] = None
    llm_port: Optional[int] = None
    timeout_seconds: Optional[int] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""
    status: Literal["error"]
    code: str = Field(description="Error code (e.g., INVALID_REQUEST, LLM_UNAVAILABLE)")
    error: str = Field(description="Human-readable error message")
    details: Optional[ErrorDetail] = None
