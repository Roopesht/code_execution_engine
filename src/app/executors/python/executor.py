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
        """Parse pytest output to extract test results"""
        lines = logs.split("\n")
        test_results = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for line in lines:
            # Parse test results (e.g., "test_name PASSED", "test_name FAILED")
            if " PASSED" in line or " FAILED" in line:
                parts = line.split("::")
                if len(parts) >= 2:
                    test_name = parts[-1].split()[0]
                    status = "Passed" if "PASSED" in line else "Failed"
                    test_results.append({
                        "name": test_name,
                        "status": status
                    })
                    total_tests += 1
                    if status == "Passed":
                        passed_tests += 1
                    else:
                        failed_tests += 1

        # Parse summary line (e.g., "5 passed in 0.25s")
        for line in lines:
            if "passed" in line and "==" in line:
                if "failed" in line:
                    # Parse "X failed, Y passed"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "failed,":
                            failed_tests = int(parts[i-1])
                        if part == "passed":
                            passed_tests = int(parts[i-1])
                    total_tests = passed_tests + failed_tests
                break

        return {
            "passed": failed_tests == 0 and total_tests > 0,
            "totalTests": total_tests,
            "passedTests": passed_tests,
            "failedTests": failed_tests,
            "tests": test_results,
            "error": None if failed_tests == 0 else {
                "type": "TestFailure",
                "message": f"{failed_tests} test(s) failed"
            }
        }
