@echo off
chcp 65001 >nul
echo ============================================================
echo   Odoo MCP Unified - Installation Script
echo ============================================================
echo.

echo [1/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [4/4] Installing package...
pip install -e .

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure your settings
echo 2. For Claude Desktop: Update claude_desktop_config.json
echo 3. For local testing: Run test.bat
echo 4. For Zeabur: Push to GitHub and deploy
echo.
pause
