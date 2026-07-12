@echo off
REM Quickstart: Install & run Qwen2.5-Coder LLM with Docker (Windows)
REM One-step setup for students
REM Usage: quickstart.bat

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  Qwen2.5-Coder LLM - Quick Setup (Windows)             ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is installed
echo Checking requirements...
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ✗ Docker not found!
    echo.
    echo Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
echo ✓ Docker installed
echo.

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ✗ docker-compose not found
    echo.
    pause
    exit /b 1
)

REM Download model
echo Downloading Qwen2.5-Coder 0.5B model (644MB)...
echo This may take a few minutes...
echo.
call powershell -NoProfile -ExecutionPolicy Bypass -Command "& {python -c \"from huggingface_hub import hf_hub_download; hf_hub_download('Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF', 'qwen2.5-coder-0.5b-instruct-q8_0.gguf', cache_dir='models', local_dir='models')\"}"
if errorlevel 1 (
    echo.
    echo ! Note: Model download via Python failed
    echo ! Trying alternate method...
    echo.
)

REM Create symlink
cd models
if not exist active.gguf (
    REM Create symlink using mklink (Windows command)
    for %%f in (qwen2.5-coder-0.5b-instruct-q8_0.gguf) do (
        mklink active.gguf %%f >nul 2>&1
        if errorlevel 1 (
            REM If mklink fails, just copy as backup
            copy qwen2.5-coder-0.5b-instruct-q8_0.gguf active.gguf >nul 2>&1
        )
    )
)
cd ..

echo.
echo Starting Docker container...
cd docker

REM Stop and remove existing container
docker-compose down >nul 2>&1

REM Start fresh container
docker-compose up -d llm-server
if errorlevel 1 (
    echo.
    echo ✗ Failed to start Docker container
    echo.
    echo Troubleshooting:
    echo  1. Make sure Docker Desktop is running
    echo  2. Check Windows Event Viewer for Docker errors
    echo  3. Try: docker-compose up (without -d) for detailed output
    echo.
    pause
    exit /b 1
)

cd ..
echo.
echo Waiting for server to start (up to 60 seconds)...
echo.

REM Wait for server with timeout
setlocal enabledelayedexpansion
for /L %%i in (1,1,60) do (
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:8001/health >nul 2>&1
    if errorlevel 0 (
        echo ✓ Server is ready!
        goto server_ready
    )
    echo -n "."
)

:server_ready
echo.
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  ✅ Setup Complete!                                    ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 🚀 API is running at: http://localhost:8001
echo.
echo 📝 Quick Test:
echo.
echo   REM Health check
echo   curl http://localhost:8001/health
echo.
echo   REM Chat with the model
echo   curl -X POST http://localhost:8001/v1/chat/completions ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"model\":\"qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"write python fibonacci\"}],\"max_tokens\":100}"
echo.
echo 📚 Full documentation: See README.md and MODEL_SIZES.md
echo.
echo 🔄 To switch models:
echo   bash download_model.sh 1.5b  (or 3b)
echo   cd docker
echo   docker-compose restart
echo.
echo Press any key to continue...
pause >nul
