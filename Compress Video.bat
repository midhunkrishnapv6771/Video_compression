@echo off
setlocal
title AptiTalent - Tutor Video Compressor Web Server

echo ========================================================================
echo   AptiTalent Tutor Educational Video Compressor Engine
echo ========================================================================
echo.
echo [1/2] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.8+.
    pause
    exit /b 1
)

echo [2/2] Launching Local Compressor Web Application...
echo.
echo  ----------------------------------------------------------------------
echo   Server URL : http://localhost:8765
echo   Saved Files: Compressed\
echo  ----------------------------------------------------------------------
echo.
echo Opening web interface in your default browser...

start "" "http://localhost:8765"

python "%~dp0main.py" server

if errorlevel 1 (
    echo.
    echo [ERROR] Server shut down unexpectedly.
    echo.
    pause
)