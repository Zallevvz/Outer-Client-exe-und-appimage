#!/usr/bin/env bash
set -euo pipefail

VERSION="4.8"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== OuterClient ${VERSION}: AppImage build =="

rm -rf build dist dist-release
mkdir -p dist-release build

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name OuterClient \
  --add-data "assets:assets" \
  --collect-all customtkinter \
  --collect-all minecraft_launcher_lib \
  outerclient.py

APPDIR="$ROOT/build/OuterClient.AppDir"
mkdir -p "$APPDIR/usr/bin"
cp -a "$ROOT/dist/OuterClient/." "$APPDIR/usr/bin/"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env sh
set -e
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/OuterClient" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/outerclient.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec=OuterClient
Icon=outerclient
Terminal=false
Categories=Game;
StartupWMClass=OuterClient
EOF

cp "$ROOT/assets/outerclient-logo.png" "$APPDIR/outerclient.png"

mkdir -p "$APPDIR/usr/share/icons/hicolor/512x512/apps"
cp "$ROOT/assets/outerclient-logo.png" \
  "$APPDIR/usr/share/icons/hicolor/512x512/apps/outerclient.png"

APPIMAGETOOL="$ROOT/build/appimagetool-x86_64.AppImage"

curl -fL \
  "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
  -o "$APPIMAGETOOL"

chmod +x "$APPIMAGETOOL"

OUTPUT="$ROOT/dist-release/OuterClient-v${VERSION}-x86_64.AppImage"

ARCH=x86_64 \
APPIMAGE_EXTRACT_AND_RUN=1 \
"$APPIMAGETOOL" "$APPDIR" "$OUTPUT"

chmod +x "$OUTPUT"

echo
echo "Built:"
ls -lh "$OUTPUT"
