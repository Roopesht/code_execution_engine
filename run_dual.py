#!/usr/bin/env python3
"""Run both HTTP and HTTPS servers simultaneously"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import config after loading env
from src.app.utils.config import Config
from src.app.main import app

def run_servers():
    """Start HTTP and HTTPS servers"""
    processes = []

    # Check for SSL certificates
    cert_path = Path("/app/certs/cert.pem")
    key_path = Path("/app/certs/key.pem")
    has_ssl = cert_path.exists() and key_path.exists()

    # HTTP Server
    print(f"🌐 Starting HTTP server on {Config.HOST}:{Config.PORT}")
    http_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.app.main:app",
        f"--host={Config.HOST}",
        f"--port={Config.PORT}"
    ]
    http_process = subprocess.Popen(http_cmd)
    processes.append(("HTTP", http_process))

    # HTTPS Server (if certificates exist)
    if has_ssl:
        print(f"🔒 Starting HTTPS server on {Config.HOST}:{Config.HTTPS_PORT}")
        https_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.app.main:app",
            f"--host={Config.HOST}",
            f"--port={Config.HTTPS_PORT}",
            "--ssl-certfile=/app/certs/cert.pem",
            "--ssl-keyfile=/app/certs/key.pem"
        ]
        https_process = subprocess.Popen(https_cmd)
        processes.append(("HTTPS", https_process))
        print("✓ Both HTTP and HTTPS servers running")
    else:
        print("⚠ SSL certificates not found - HTTPS not available")
        print("✓ HTTP server running")

    # Wait for all processes
    try:
        for name, process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n⚠ Shutting down servers...")
        for name, process in processes:
            process.terminate()
        for name, process in processes:
            process.wait()

if __name__ == "__main__":
    run_servers()
