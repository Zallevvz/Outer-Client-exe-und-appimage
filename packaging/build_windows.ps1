$ErrorActionPreference = "Stop"

$Version = "4.8"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "== OuterClient $Version : Windows EXE build =="

Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist-release -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force dist-release | Out-Null

python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name OuterClient `
  --icon "assets/outerclient.ico" `
  --version-file "packaging/version_info.txt" `
  --add-data "assets:assets" `
  --collect-all customtkinter `
  --collect-all minecraft_launcher_lib `
  outerclient.py

$Output = "dist-release/OuterClient-v$Version-windows-x86_64.exe"
Move-Item "dist/OuterClient.exe" $Output -Force

Write-Host ""
Write-Host "Built:"
Get-Item $Output | Format-List Name, Length, FullName
