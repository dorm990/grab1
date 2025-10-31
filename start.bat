@echo off
echo =======================================
echo  Duck Business Game - Start
echo =======================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed
    pause
    exit /b 1
)

REM Install dependencies
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [OK] Dependencies installed
echo.

REM Start Flask
echo [INFO] Starting web server...
start /B python webapp.py

REM Wait
timeout /t 3 /nobreak >nul

REM Start Bot
echo [INFO] Starting Telegram bot...
python bot.py

pause
