import json
from typing import Type
from ..models import ExecutionRequest, ExecutionResponse, TestResult
from ..executors.base import BaseExecutor
from ..executors.python import PythonExecutor
from ..utils.logger import get_logger

logger = get_logger(__name__)

EXECUTORS = {
    "python": PythonExecutor,
    "javascript": None,  # TODO: Implement JavaScriptExecutor
}


async def execute_code(request: ExecutionRequest) -> ExecutionResponse:
    """Execute code and return results"""
    executor_class = EXECUTORS.get(request.language)

    if not executor_class:
        logger.error(json.dumps({
            "event": "execution_unsupported_language",
            "language": request.language
        }))
        raise ValueError(f"Unsupported language: {request.language}")

    executor = executor_class()
    workspace = None

    try:
        # Prepare workspace
        logger.info(json.dumps({
            "event": "execution_preparing",
            "exerciseId": request.exerciseId,
            "language": request.language
        }))
        workspace = await executor.prepare(request.code, request.tests)

        # Execute code
        logger.info(json.dumps({
            "event": "execution_running",
            "exerciseId": request.exerciseId,
            "workspace": workspace
        }))
        execution_result = await executor.execute(workspace)

        # Collect results
        logger.info(json.dumps({
            "event": "execution_collecting_results",
            "exerciseId": request.exerciseId
        }))
        results = await executor.collect_results(
            workspace,
            execution_result.get("logs", "")
        )

        # Format response
        logger.info(json.dumps({
            "event": "execution_complete",
            "exerciseId": request.exerciseId,
            "passed": results.get("passed")
        }))

        return ExecutionResponse(
            passed=results.get("passed", False),
            totalTests=results.get("totalTests", 0),
            passedTests=results.get("passedTests", 0),
            failedTests=results.get("failedTests", 0),
            executionTime=round(execution_result.get("execution_time", 0.0), 2),
            memory=0,  # TODO: Get from Docker stats
            stdout=execution_result.get("logs", ""),
            stderr="",
            tests=[
                TestResult(
                    name=t.get("name", ""),
                    status=t.get("status", "Failed"),
                    error=t.get("error")
                )
                for t in results.get("tests", [])
            ],
            error=results.get("error")
        )

    except Exception as e:
        logger.error(json.dumps({
            "event": "execution_failed",
            "exerciseId": request.exerciseId,
            "error": str(e)
        }))

        return ExecutionResponse(
            passed=False,
            totalTests=0,
            passedTests=0,
            failedTests=0,
            executionTime=0.0,
            memory=0,
            stdout="",
            stderr=str(e),
            tests=[],
            error={
                "type": "ExecutionError",
                "message": str(e)
            }
        )

    finally:
        if workspace:
            await executor.cleanup(workspace)
