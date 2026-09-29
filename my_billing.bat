@echo off
title My Billing System
color 0A
cls
echo ========================================
echo        🧾 MY BILLING SYSTEM
echo ========================================
echo.
echo 📂 Current Folder: C:\Users\ADMIN\mini_billing_system
echo.
echo 🔄 Activating virtual environment...
cd /d "C:\Users\ADMIN\mini_billing_system"
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated!
echo.
echo 🚀 Starting Flask application...
echo.
echo ========================================
echo    🌐 Open your browser and go to:
echo        http://127.0.0.1:5000
echo ========================================
echo.
echo ⚠️  Press CTRL+C to stop the server
echo.
python app.py