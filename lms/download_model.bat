@echo off
REM Download Qwen2.5-Coder model for local LLM service
REM Supports multiple model sizes: 0.5B (fastest), 1.5B (balanced), 3.0B (best quality)
REM Usage: download_model.bat [0.5b|1.5b|3b]

setlocal enabledelayedexpansion

set "MODELS_DIR=%~dp0models"
set "MODEL_SIZE=%1"
if "!MODEL_SIZE!"=="" set "MODEL_SIZE=0.5b"

mkdir "!MODELS_DIR!" 2>nul

REM Parse model size
if /i "!MODEL_SIZE!"=="0.5b" (
    set "MODEL_NAME=qwen2.5-coder-0.5b"
    set "FILENAME=qwen2.5-coder-0.5b-instruct-q8_0.gguf"
    set "REPO=Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF"
    echo Selected: 0.5B model ^(fastest, ~400MB, 512M params^)
) else if /i "!MODEL_SIZE!"=="1.5b" (
    set "MODEL_NAME=qwen2.5-coder-1.5b"
    set "FILENAME=qwen2.5-coder-1.5b-q8_0.gguf"
    set "REPO=ggml-org/Qwen2.5-Coder-1.5B-Q8_0-GGUF"
    echo Selected: 1.5B model ^(balanced, ~1.5GB, 1.5B params^)
) else if /i "!MODEL_SIZE!"=="3b" (
    set "MODEL_NAME=qwen2.5-coder-3b"
    set "FILENAME=qwen2.5-coder-3b-q8_0.gguf"
    set "REPO=ggml-org/Qwen2.5-Coder-3B-Q8_0-GGUF"
    echo Selected: 3.0B model ^(best quality, ~3.4GB, 3.0B params^)
) else if /i "!MODEL_SIZE!"=="3.0b" (
    set "MODEL_NAME=qwen2.5-coder-3b"
    set "FILENAME=qwen2.5-coder-3b-q8_0.gguf"
    set "REPO=ggml-org/Qwen2.5-Coder-3B-Q8_0-GGUF"
    echo Selected: 3.0B model ^(best quality, ~3.4GB, 3.0B params^)
) else (
    echo Usage: %~nx0 [0.5b^|1.5b^|3b]
    echo.
    echo Model sizes:
    echo   0.5b - Ultra-fast ^(~400MB, 512M params, ~1 sec per response^)
    echo   1.5b - Balanced ^(~1.5GB, 1.5B params, ~3-5 sec per response^)
    echo   3b   - Best quality ^(~3.4GB, 3.0B params, ~10-15 sec per response^)
    exit /b 1
)

set "OUTPUT_FILE=!MODELS_DIR!\!FILENAME!"

REM Check if model already exists
if exist "!OUTPUT_FILE!" (
    for /F "usebackq" %%A in ('powershell -NoProfile -Command "if ((Get-Item '!OUTPUT_FILE!').Length -gt 0) { Write-Host 'exists' }"') do (
        if "%%A"=="exists" (
            echo ✓ Model already exists: !OUTPUT_FILE!
            cd /d "!MODELS_DIR!"
            mklink active.gguf "!FILENAME!" >nul 2>&1
            if errorlevel 1 (
                copy "!FILENAME!" active.gguf >nul 2>&1
            )
            echo ✓ Symlink ready: active.gguf
            exit /b 0
        )
    )
)

echo Downloading Qwen2.5-Coder-!MODEL_SIZE! model...
echo File: !FILENAME!
echo Destination: !MODELS_DIR!
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found. Please install Python 3.8+
    echo   Visit: https://www.python.org/downloads/
    exit /b 1
)

REM Install huggingface-hub if needed
python -c "import huggingface_hub" >nul 2>&1
if errorlevel 1 (
    echo Installing huggingface-hub...
    python -m pip install -q huggingface-hub
    if errorlevel 1 (
        echo ✗ Failed to install huggingface-hub
        exit /b 1
    )
)

REM Download using huggingface-hub
echo Downloading from !REPO!...
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('!REPO!', '!FILENAME!', cache_dir='!MODELS_DIR!', local_dir='!MODELS_DIR!')"
if errorlevel 1 (
    echo ✗ Download failed
    exit /b 1
)

REM Create symlink
cd /d "!MODELS_DIR!"
mklink active.gguf "!FILENAME!" >nul 2>&1
if errorlevel 1 (
    copy "!FILENAME!" active.gguf >nul 2>&1
)

echo.
echo ✓ Download complete!
echo   File: !FILENAME!
echo ✓ Symlink created: active.gguf
echo.
echo Ready to start! Run:
echo   cd lms\docker
echo   docker-compose up -d llm-server
exit /b 0
