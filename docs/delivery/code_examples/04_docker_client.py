# Docker Integration
# Location: app/utils/docker_client.py

import docker
import os
import uuid


class DockerExecutor:
    def __init__(self):
        self.client = docker.from_env()

    async def create_workspace(self) -> str:
        """Create temp workspace, return path"""
        workspace_id = str(uuid.uuid4())
        workspace_path = f"/tmp/executor_{workspace_id}"
        os.makedirs(workspace_path, exist_ok=True)
        return workspace_path

    async def run_container(self, image, workspace, command):
        """Run code in container with resource limits"""
        container = self.client.containers.run(
            image,
            command,
            volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
            memory=512 * 1024 * 1024,  # 512 MB
            cpus=0.5,
            network_disabled=True,
            remove=True,  # Auto cleanup
            stdout=True,
            stderr=True,
            timeout=30  # 30 second total timeout
        )
        return container
