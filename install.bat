@echo off
title PixelProTech Drive Manager — Installer
color 0A

echo.
echo ============================================================
echo   PIXELPROTECH SOLUTIONS — DRIVE MANAGER INSTALLER
echo   IT Support . Computer Repairs . Gauteng
echo   076 645 9348 . pixelprotechsolutions@gmail.com
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found on this machine.
    echo [i] Opening python.org to download Python...
    timeout /t 2 >nul
    start https://www.python.org/downloads/
    echo.
    echo [!] After installing Python, run this installer again.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detected.
echo.

:: Install psutil
echo [..] Installing required dependency: psutil...
python -m pip install psutil --quiet
if %errorlevel% neq 0 (
    echo [!] Failed to install psutil. Check your internet connection.
    pause
    exit /b 1
)
echo [OK] psutil installed.
echo.

:: Check if the .py file exists in same folder
if not exist "%~dp0PixelProTech_DriveManager.py" (
    echo [!] PixelProTech_DriveManager.py not found in this folder.
    echo [i] Make sure install.bat and PixelProTech_DriveManager.py
    echo     are in the same folder, then try again.
    echo.
    pause
    exit /b 1
)

echo [OK] PixelProTech_DriveManager.py found.
echo.
echo ============================================================
echo   ALL DONE. Launching Drive Manager now...
echo ============================================================
echo.
timeout /t 2 >nul

python "%~dp0PixelProTech_DriveManager.py"
