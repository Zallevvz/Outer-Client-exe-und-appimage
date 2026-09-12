$ErrorActionPreference = "Stop"

$Version = "6.3.6"

py -3.13 -m venv .build-venv
& .\.build-venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

python -c "import PIL, PIL.ImageTk, PIL._tkinter_finder, tkinter; print('PIL._tkinter_finder OK')"

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
  --collect-all PIL `
  --hidden-import PIL.ImageTk `
  --hidden-import PIL._tkinter_finder `
  outerclient.py

Write-Host "Gotowe: dist\OuterClient-v$Version.exe"
