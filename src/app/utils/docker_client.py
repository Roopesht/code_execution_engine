import os
import uuid
import asyncio
import subprocess
import shutil
from asyncio import Lock

docker_execution_lock = Lock()


class DockerExecutor:
    def __init__(self):
        pass

    async def create_workspace(self) -> str:
        """Create temp workspace, return path"""
        workspace_id = str(uuid.uuid4())
        workspace_path = f"/tmp/executor_{workspace_id}"
        os.makedirs(workspace_path, exist_ok=True)
        return workspace_path

    async def run_container(self, image: str, workspace: str, command: str, timeout: int = 5):
        """Run code directly using subprocess with timeout"""
        loop = asyncio.get_event_loop()

        async with docker_execution_lock:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    command,
                    shell=True,
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            )
            return result

    async def cleanup_workspace(self, workspace: str):
        """Remove workspace directory"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: shutil.rmtree(workspace, ignore_errors=True)
        )
