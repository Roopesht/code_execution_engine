#!/usr/bin/env python3
"""Run the execution engine server"""

import sys
from dotenv import load_dotenv
import uvicorn
from src.app.main import app
from src.app.utils.config import Config

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_config=None
    )
