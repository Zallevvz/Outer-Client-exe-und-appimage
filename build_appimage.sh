#!/usr/bin/env bash
set -euo pipefail

VERSION="4.9.2"

python3 -m venv .build-venv
source .build-venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

rm -rf build dist AppDir
rm -f ./*.spec OuterClient-*.AppImage

pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  --windowed \
  --name OuterClient \
  --add-data "assets:assets" \
  --collect-all customtkinter \
  --collect-all minecraft_launcher_lib \
  outerclient.py

mkdir -p AppDir/usr/bin/OuterClient
cp -a dist/OuterClient/. AppDir/usr/bin/OuterClient/
cp assets/outerclient-logo.png AppDir/outerclient.png

cat > AppDir/OuterClient.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=OuterClient 4.9.2
Comment=OuterClient Minecraft Launcher
Exec=OuterClient
Icon=outerclient
Categories=Game;
Terminal=false
StartupWMClass=OuterClient
X-AppImage-Version=4.9.2
EOF

cat > AppDir/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/OuterClient/OuterClient" "$@"
EOF

chmod +x AppDir/AppRun
chmod +x AppDir/usr/bin/OuterClient/OuterClient

if [[ ! -f appimagetool.AppImage ]]; then
  curl -L \
    https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage \
    -o appimagetool.AppImage
  chmod +x appimagetool.AppImage
fi

ARCH=x86_64 VERSION="$VERSION" APPIMAGE_EXTRACT_AND_RUN=1 \
  ./appimagetool.AppImage \
  AppDir \
  "OuterClient-v${VERSION}-x86_64.AppImage"

chmod +x "OuterClient-v${VERSION}-x86_64.AppImage"
echo "Gotowe: OuterClient-v${VERSION}-x86_64.AppImage"
