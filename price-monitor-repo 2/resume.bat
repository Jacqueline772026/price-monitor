@echo off
chcp 65001 >nul
cd /d "%~dp0"
.venv\Scripts\python app\run_all.py --mode continue
echo.
pause
