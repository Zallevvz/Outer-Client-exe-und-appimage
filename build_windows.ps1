$ErrorActionPreference = "Stop"

$Version = "4.9.2"

py -3.13 -m venv .build-venv
& .\.build-venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force *.spec -ErrorAction SilentlyContinue

pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "OuterClient-v$Version" `
  --icon assets\outerclient.ico `
  --add-data "assets;assets" `
  --collect-all customtkinter `
  --collect-all minecraft_launcher_lib `
  outerclient.py

Write-Host "Gotowe: dist\OuterClient-v$Version.exe"
