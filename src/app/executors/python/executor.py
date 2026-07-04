import os
import uuid
import json
import shutil
import asyncio
import subprocess
import time
from pathlib import Path
from ..base import BaseExecutor
from ...utils.docker_client import DockerExecutor, docker_execution_lock
from ...utils.logger import get_logger
from ...utils.error_formatter import ErrorFormatter

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
        """Execute code using pytest via subprocess"""
        start_time = time.time()
        loop = asyncio.get_event_loop()

        try:
            # Run pytest in workspace with timeout
            result = await self.docker.run_container(
                image=None,  # Not used with subprocess approach
                workspace=workspace,
                command="pytest test_solution.py -v --tb=short",
                timeout=5
            )

            execution_time = time.time() - start_time
            logs = result.stdout + result.stderr

            logger.info(json.dumps({
                "event": "python_execution_complete",
                "workspace": workspace,
                "execution_time": execution_time,
                "return_code": result.returncode
            }))

            return {
                "workspace": workspace,
                "logs": logs,
                "execution_time": execution_time
            }

        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            logger.error(json.dumps({
                "event": "python_execution_timeout",
                "workspace": workspace,
                "execution_time": execution_time,
                "error": str(e)
            }))
            raise

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(json.dumps({
                "event": "python_execution_failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "workspace": workspace,
                "execution_time": execution_time
            }))
            raise

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
        import re

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

        # First pass: collect test results
        test_map = {}
        for line in lines:
            # Match test result lines: "test_solution.py::test_name PASSED/FAILED"
            test_match = re.search(r'(test_\w+\.py)::(test_\w+)\s+(PASSED|FAILED)', line)
            if test_match:
                test_name = test_match.group(2)
                status = "Passed" if test_match.group(3) == "PASSED" else "Failed"
                test_map[test_name] = {
                    "name": test_name,
                    "status": status,
                    "failure_lines": []
                }
                total_tests += 1
                if status == "Passed":
                    passed_tests += 1
                else:
                    failed_tests += 1

        # Second pass: collect failure details from FAILURES section
        current_failed_test = None
        in_failures_section = False

        for line in lines:
            if "=== FAILURES ===" in line:
                in_failures_section = True
                continue

            if in_failures_section:
                # Look for test name in failure header (surrounded by underscores)
                # Format: "_________________________________ test_name _________________________________"
                test_match = re.search(r'test_\w+', line)
                if test_match and line.count("_") > 5:
                    current_failed_test = test_match.group(0)

                # Collect error lines for the current failed test
                if current_failed_test and current_failed_test in test_map:
                    if line.startswith("E   "):
                        test_map[current_failed_test]["failure_lines"].append(line[4:].strip())

        # Build test results with parsed failure details
        for test_name in test_map:
            test_data = test_map[test_name]
            test_result = {
                "name": test_name,
                "status": test_data["status"],
                "expected": None,
                "actual": None,
                "error": None,
                "stackTrace": None
            }

            if test_data["status"] == "Failed" and test_data["failure_lines"]:
                failure_details = self._parse_failure_output(test_data["failure_lines"])
                # Update only fields that were found
                for key in ["error", "expected", "actual", "stackTrace"]:
                    if key in failure_details:
                        test_result[key] = failure_details[key]

            test_results.append(test_result)

        # Parse summary line for accurate counts
        for line in lines:
            if "passed" in line.lower() and ("failed" in line.lower() or "==" in line):
                counts = self._parse_summary_line(line)
                if counts:
                    passed_tests = counts.get("passed", passed_tests)
                    failed_tests = counts.get("failed", failed_tests)
                    total_tests = passed_tests + failed_tests
                break

        # Handle edge case: no tests found
        if total_tests == 0:
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
        """Extract syntax/import errors from pytest output using ErrorFormatter"""
        if "SyntaxError" in logs:
            return ErrorFormatter.format_syntax_error(logs)

        if "ImportError" in logs or "ModuleNotFoundError" in logs:
            return ErrorFormatter.format_import_error(logs)

        if "ERRORS" in logs or "ERROR" in logs:
            # Try to detect timeout
            if "timeout" in logs.lower() or "exceeded" in logs.lower():
                return ErrorFormatter.format_timeout_error()
            return ErrorFormatter.format_docker_error(logs)

        return None

    def _parse_failure_output(self, failure_lines: list) -> dict:
        """Extract human-readable error details from pytest error output lines"""
        import re

        result = {}

        if not failure_lines:
            return result

        # Process each error line from pytest output (lines starting with "E ")
        for line in failure_lines:
            # Look for assertion failures: "assert False == True"
            if "assert" in line and "==" in line:
                result["error"] = line
                # Parse expected vs actual from assertion
                parts = line.split("==")
                if len(parts) == 2:
                    result["actual"] = parts[0].replace("assert", "").strip()
                    result["expected"] = parts[1].strip()

            # Look for where clause: "+ where False = is_even(3)"
            elif "where" in line:
                # Extract the comparison info: "where False = is_even(3)"
                match = re.search(r'where\s+(\S+)\s*=\s*(.+)', line)
                if match:
                    actual_val = match.group(1)
                    function_call = match.group(2)
                    if "actual" not in result:
                        result["actual"] = actual_val
                    # Add more context to error message
                    if "error" not in result:
                        result["error"] = f"Assertion failed: actual={actual_val}, from {function_call}"
                    result["stackTrace"] = line

            # Collect other error information (AssertionError, etc)
            elif line and "error" not in result:
                result["error"] = line

        # Ensure we have a primary error message
        if not result.get("error") and failure_lines:
            result["error"] = " ".join(failure_lines)

        return result

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
