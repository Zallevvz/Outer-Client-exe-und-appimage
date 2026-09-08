@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
    echo Najpierw uruchom install_windows.bat
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python outerclient.py
pause
