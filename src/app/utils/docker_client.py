import docker
import os
import uuid
import asyncio
from asyncio import Lock

docker_execution_lock = Lock()


class DockerExecutor:
    def __init__(self):
        self.client = docker.from_env()

    async def create_workspace(self) -> str:
        """Create temp workspace, return path"""
        workspace_id = str(uuid.uuid4())
        workspace_path = f"/tmp/executor_{workspace_id}"
        os.makedirs(workspace_path, exist_ok=True)
        return workspace_path

    async def run_container(self, image: str, workspace: str, command: str, timeout: int = 5):
        """Run code in container with resource limits"""
        loop = asyncio.get_event_loop()

        async with docker_execution_lock:
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.run(
                    image,
                    command,
                    volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
                    mem_limit="512m",
                    nano_cpus=int(0.5 * 1e9),
                    network_disabled=True,
                    remove=False,
                    stdout=True,
                    stderr=True
                )
            )
            return container

    async def cleanup_workspace(self, workspace: str):
        """Remove workspace directory"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: __import__('shutil').rmtree(workspace, ignore_errors=True)
        )
