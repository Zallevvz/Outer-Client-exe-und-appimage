# OuterClient v4.8 — AppImage + EXE

## Najłatwiej: GitHub Actions

Repo może być **prywatne**.

1. Utwórz prywatne repo.
2. Wrzuć całą zawartość tej paczki.
3. Wejdź w **Actions**.
4. Otwórz **Build OuterClient binaries**.
5. Kliknij **Run workflow**.
6. Po zakończeniu pobierz artifacts:
   - `OuterClient-v4.8-AppImage`
   - `OuterClient-v4.8-Windows`

Dostaniesz:
- `OuterClient-v4.8-x86_64.AppImage`
- `OuterClient-v4.8-windows-x86_64.exe`

Workflow odpala się też po wysłaniu taga, np. `v4.8`.

## Lokalny AppImage na Linuxie

```bash
python -m venv .build-venv
source .build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller==6.22.2
chmod +x packaging/build_appimage.sh
./packaging/build_appimage.sh
```

Wynik:
`dist-release/OuterClient-v4.8-x86_64.AppImage`

## Lokalny EXE na Windows

Uruchom:
`packaging\\build_windows.bat`

albo:

```powershell
py -3.13 -m venv .build-venv
.build-venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller==6.22.2
.\\packaging\\build_windows.ps1
```

Wynik:
`dist-release\\OuterClient-v4.8-windows-x86_64.exe`

## Ważne

PyInstaller nie jest cross-kompilatorem:
- AppImage budujemy na GNU/Linux,
- EXE budujemy na Windows.

Dlatego workflow ma dwa osobne joby.

Java nie jest bundlowana. OuterClient nadal korzysta z Javy wybranej
w ustawieniach launchera.
