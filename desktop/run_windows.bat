@echo off
REM AselCam Desktop - Windows Launcher
title AselCam Virtual Camera Studio

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 was not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/ and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [AselCam] Checking Python dependencies...
python -m pip install -q -r requirements.txt

echo [AselCam] Launching AselCam Studio...
set PYTHONPATH=%~dp0
python -m aselcam.main

if %ERRORLEVEL% neq 0 (
    echo.
    echo [AselCam] Program exited with error code %ERRORLEVEL%.
    pause
)
