@echo off
color 0A
title 🧾 Mini Billing System
cls
echo ========================================
echo       🧾 MINI BILLING SYSTEM
echo ========================================
echo.
cd /d "%~dp0"
echo 📁 Current Folder: %cd%
echo.
echo 🔄 Activating virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated!
) else (
    echo ❌ ERROR: venv not found!
    echo Please run: python -m venv venv
    pause
    exit
)
echo.
echo 🚀 Starting Flask application...
echo.
echo ========================================
echo    🌐 Open: http://127.0.0.1:5000
echo ========================================
echo.
echo ⚠️  Press CTRL+C to stop the server
echo.
python app.py
pause