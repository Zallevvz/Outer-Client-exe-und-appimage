#!/bin/sh
set -e
cd "$(dirname "$0")"
if [ ! -f .venv/bin/activate ]; then
    echo "Brak .venv. Uruchom najpierw ./install_linux.sh"
    exit 1
fi
. .venv/bin/activate
exec python outerclient.py
