from abc import ABC, abstractmethod


class BaseExecutor(ABC):
    """Abstract base class for code executors"""

    @abstractmethod
    async def prepare(self, code: str, tests: str) -> str:
        """Prepare execution environment. Returns workspace path."""
        pass

    @abstractmethod
    async def execute(self, workspace: str) -> dict:
        """Execute code. Returns results."""
        pass

    @abstractmethod
    async def collect_results(self, workspace: str) -> dict:
        """Collect execution results."""
        pass

    @abstractmethod
    async def cleanup(self, workspace: str) -> None:
        """Clean up temporary files."""
        pass
