#!/bin/sh
set -e
sudo pacman -S --needed python python-pip tk jre17-openjdk jre21-openjdk
cd "$(dirname "$0")"
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "OuterClient v6.0 zainstalowany."


DIR="$(pwd)"
mkdir -p "$HOME/.local/share/applications"

cat > "$HOME/.local/share/applications/outerclient.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=OuterClient
Comment=OuterClient Minecraft Launcher
Exec=$DIR/run_outerclient.sh
Path=$DIR
Icon=$DIR/assets/outerclient-logo.png
Terminal=false
Categories=Game;
StartupWMClass=OuterClient
EOF

chmod +x "$HOME/.local/share/applications/outerclient.desktop"

echo "Dodano skrót OuterClient z nowym logo do menu aplikacji."
