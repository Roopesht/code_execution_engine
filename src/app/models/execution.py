from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class ExecutionRequest(BaseModel):
    language: Literal["python", "javascript"]
    exerciseId: str = Field(min_length=1, max_length=255, pattern="^[a-z0-9_]+$")
    code: str = Field(min_length=1, max_length=1_000_000)
    tests: str = Field(min_length=1, max_length=1_000_000)
    timeout: Optional[int] = Field(default=5, ge=1, le=30)


class TestResult(BaseModel):
    name: str
    status: Literal["Passed", "Failed"]
    expected: Optional[str] = None
    actual: Optional[str] = None
    error: Optional[str] = None
    stackTrace: Optional[str] = None


class ErrorInfo(BaseModel):
    type: str
    message: str
    line: Optional[int] = None
    stackTrace: Optional[str] = None


class ExecutionResponse(BaseModel):
    passed: bool
    totalTests: int
    passedTests: int
    failedTests: int
    executionTime: float
    memory: int
    stdout: str
    stderr: str
    tests: List[TestResult]
    error: Optional[ErrorInfo] = None
