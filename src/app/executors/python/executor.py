import os
import uuid
import json
import shutil
import asyncio
import time
from pathlib import Path
from ..base import BaseExecutor
from ...utils.docker_client import DockerExecutor, docker_execution_lock
from ...utils.logger import get_logger

logger = get_logger(__name__)


class PythonExecutor(BaseExecutor):
    """Python code executor with pytest support"""

    def __init__(self):
        self.docker = DockerExecutor()

    async def prepare(self, code: str, tests: str) -> str:
        """Prepare execution environment with code and tests"""
        workspace = await self.docker.create_workspace()

        try:
            # Write user code
            code_path = Path(workspace) / "user_code.py"
            code_path.write_text(code, encoding="utf-8")

            # Write test code
            test_path = Path(workspace) / "test_solution.py"
            test_path.write_text(tests, encoding="utf-8")

            logger.info(json.dumps({
                "event": "python_workspace_prepared",
                "workspace": workspace
            }))

            return workspace
        except Exception as e:
            # Cleanup on error
            await self.cleanup(workspace)
            logger.error(json.dumps({
                "event": "python_prepare_failed",
                "error": str(e)
            }))
            raise

    async def execute(self, workspace: str) -> dict:
        """Execute code in Docker container using pytest"""
        start_time = time.time()
        container = None
        logs = None
        loop = asyncio.get_event_loop()

        try:
            # Run pytest in container (detach to get container object)
            async with docker_execution_lock:
                container = await loop.run_in_executor(
                    None,
                    lambda: self.docker.client.containers.run(
                        "executor-python:latest",
                        "pytest /workspace/test_solution.py -v --tb=short",
                        volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
                        mem_limit="512m",
                        nano_cpus=int(0.5 * 1e9),
                        network_disabled=True,
                        remove=False,
                        detach=True
                    )
                )

            # Wait for container to finish
            await loop.run_in_executor(
                None,
                lambda: container.wait()
            )

            execution_time = time.time() - start_time

            # Get container logs
            logs = await loop.run_in_executor(
                None,
                lambda: container.logs(stream=False).decode("utf-8", errors="replace")
            )

            logger.info(json.dumps({
                "event": "python_execution_complete",
                "workspace": workspace,
                "execution_time": execution_time
            }))

            return {
                "workspace": workspace,
                "container": container,
                "logs": logs,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(json.dumps({
                "event": "python_execution_failed",
                "error": str(e),
                "workspace": workspace
            }))
            raise
        finally:
            if container:
                try:
                    await loop.run_in_executor(None, lambda: container.remove(force=True))
                except:
                    pass

    async def collect_results(self, workspace: str, logs: str) -> dict:
        """Collect execution results from pytest output"""
        try:
            return self._parse_pytest_output(logs)
        except Exception as e:
            logger.error(json.dumps({
                "event": "python_collect_results_failed",
                "error": str(e),
                "workspace": workspace
            }))
            return {
                "passed": False,
                "totalTests": 0,
                "passedTests": 0,
                "failedTests": 0,
                "tests": [],
                "error": {
                    "type": "ResultsCollectionError",
                    "message": str(e)
                }
            }

    async def cleanup(self, workspace: str) -> None:
        """Remove workspace directory"""
        try:
            await self.docker.cleanup_workspace(workspace)
            logger.info(json.dumps({
                "event": "python_workspace_cleaned",
                "workspace": workspace
            }))
        except Exception as e:
            logger.error(json.dumps({
                "event": "python_cleanup_failed",
                "workspace": workspace,
                "error": str(e)
            }))

    def _parse_pytest_output(self, logs: str) -> dict:
        """Parse pytest output to extract comprehensive test results"""
        lines = logs.split("\n")
        test_results = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_info = None

        # Check for syntax/import errors in output
        syntax_error_match = self._extract_error(logs)
        if syntax_error_match:
            return {
                "passed": False,
                "totalTests": 0,
                "passedTests": 0,
                "failedTests": 0,
                "tests": [],
                "error": syntax_error_match
            }

        # Parse test results line by line
        current_test = None
        in_failure_section = False

        for i, line in enumerate(lines):
            # Test result line (e.g., "test_solution.py::test_name PASSED")
            if " PASSED" in line or " FAILED" in line:
                if current_test:
                    test_results.append(current_test)

                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[-1].split()[0]
                    status = "Passed" if "PASSED" in line else "Failed"
                    current_test = {
                        "name": test_name,
                        "status": status,
                        "error": None
                    }
                    total_tests += 1
                    if status == "Passed":
                        passed_tests += 1
                    else:
                        failed_tests += 1

            # Capture failure details (error message after the test line)
            elif current_test and current_test["status"] == "Failed":
                if line.strip() and not line.startswith("="):
                    # Extract assertion or error message
                    if "AssertionError" in line or "assert" in line or "Error" in line:
                        if not current_test.get("error"):
                            current_test["error"] = line.strip()[:200]

        # Append last test if exists
        if current_test:
            test_results.append(current_test)

        # Parse summary line for final counts
        for line in lines:
            if "passed" in line.lower() and "==" in line:
                counts = self._parse_summary_line(line)
                if counts:
                    passed_tests = counts.get("passed", passed_tests)
                    failed_tests = counts.get("failed", failed_tests)
                    total_tests = passed_tests + failed_tests
                break

        # Handle edge case: no tests found
        if total_tests == 0:
            # Check if there's an error in the output
            if "ERROR" in logs or "error" in logs.lower():
                error_info = {
                    "type": "ExecutionError",
                    "message": "No tests found or execution error"
                }

        return {
            "passed": failed_tests == 0 and total_tests > 0,
            "totalTests": total_tests,
            "passedTests": passed_tests,
            "failedTests": failed_tests,
            "tests": test_results,
            "error": error_info if total_tests == 0 else (
                {
                    "type": "TestFailure",
                    "message": f"{failed_tests} test(s) failed"
                } if failed_tests > 0 else None
            )
        }

    def _extract_error(self, logs: str) -> dict | None:
        """Extract syntax/import errors from pytest output"""
        if "SyntaxError" in logs:
            lines = logs.split("\n")
            for i, line in enumerate(lines):
                if "SyntaxError" in line:
                    return {
                        "type": "SyntaxError",
                        "message": line.strip(),
                        "line": None
                    }

        if "ImportError" in logs or "ModuleNotFoundError" in logs:
            lines = logs.split("\n")
            for i, line in enumerate(lines):
                if "Error" in line and ("import" in line.lower() or "module" in line.lower()):
                    return {
                        "type": "ImportError",
                        "message": line.strip(),
                        "line": None
                    }

        if "ERRORS" in logs or "ERROR" in logs:
            lines = logs.split("\n")
            for i, line in enumerate(lines):
                if "ERROR" in line and "test" in line.lower():
                    return {
                        "type": "ExecutionError",
                        "message": line.strip(),
                        "line": None
                    }

        return None

    def _parse_summary_line(self, line: str) -> dict | None:
        """Parse pytest summary line (e.g., '4 passed in 0.12s')"""
        import re

        passed_match = re.search(r'(\d+)\s+passed', line)
        failed_match = re.search(r'(\d+)\s+failed', line)

        result = {}
        if passed_match:
            result["passed"] = int(passed_match.group(1))
        if failed_match:
            result["failed"] = int(failed_match.group(1))

        return result if result else None
