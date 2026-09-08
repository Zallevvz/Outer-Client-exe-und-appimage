@echo off
setlocal
cd /d "%~dp0\.."

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.13 -m pip install --upgrade pip
    py -3.13 -m pip install -r requirements.txt pyinstaller==6.22.2
) else (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt pyinstaller==6.22.2
)

powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
pause
