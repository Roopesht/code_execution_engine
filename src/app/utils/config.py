import os


class Config:
    # Required
    API_KEY: str = os.getenv("EXECUTOR_API_KEY")

    # CORS Configuration
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    ]

    # Optional (with defaults)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    EXECUTION_TIMEOUT: int = int(os.getenv("EXECUTION_TIMEOUT", "5"))
    CONTAINER_MEMORY_MB: int = int(os.getenv("CONTAINER_MEMORY_MB", "512"))
    CONTAINER_CPU_LIMIT: float = float(os.getenv("CONTAINER_CPU_LIMIT", "0.5"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "7999"))

    @classmethod
    def validate(cls):
        """Validate required config on startup"""
        if not cls.API_KEY:
            raise ValueError("EXECUTOR_API_KEY environment variable required")
