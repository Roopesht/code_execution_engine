#!/usr/bin/env python3
"""Run the execution engine server"""

from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from src.app.main import app
from src.app.utils.config import Config

load_dotenv()

if __name__ == "__main__":
    ssl_certfile = None
    ssl_keyfile = None
    port = Config.PORT
    protocol = "HTTP"

    # Try to load SSL certificates for HTTPS
    cert_path = Path("/app/certs/cert.pem")
    key_path = Path("/app/certs/key.pem")

    if cert_path.exists() and key_path.exists():
        try:
            ssl_certfile = str(cert_path)
            ssl_keyfile = str(key_path)
            port = Config.HTTPS_PORT
            protocol = "HTTPS"
            print(f"✓ SSL certificates loaded - {protocol} enabled on port {port}")
        except Exception as e:
            print(f"⚠ Failed to load SSL certificates: {e}")
            print(f"  Falling back to {protocol} on port {port}")
    else:
        print(f"⚠ SSL certificates not found at /app/certs/")
        print(f"  Running {protocol} on port {port}")

    uvicorn.run(
        app,
        host=Config.HOST,
        port=port,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        log_config=None
    )
