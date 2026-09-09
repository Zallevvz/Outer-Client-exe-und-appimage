# OuterClient v4.9.3

## AppImage crash naprawiony

Błąd:

`ModuleNotFoundError: No module named 'PIL._tkinter_finder'`

pochodził z builda PyInstaller. Pillow/ImageTk wymaga tego modułu do tworzenia obrazów Tk.

Build v4.9.3 dodaje:

- `--collect-all PIL`
- `--hidden-import PIL.ImageTk`
- `--hidden-import PIL._tkinter_finder`

zarówno dla Linux AppImage, jak i Windows EXE.

Workflow przed buildem dodatkowo sprawdza, czy:
- `PIL.ImageTk` się importuje,
- `PIL._tkinter_finder` się importuje,
- Tkinter jest dostępny.

## GitHub

Zastąp w repo:
- `outerclient.py`
- `.github/workflows/build-binaries.yml`
- najlepiej całą zawartość tej paczki

Następnie:

GitHub → Actions → Build and Release OuterClient 4.9.3 → Run workflow

Pobierz:
- `OuterClient-v4.9.3-x86_64.AppImage`
- `OuterClient-v4.9.3.exe`

Nie uruchamiaj starego artifactu 4.9.2.

## Fontconfig

Komunikaty `Fontconfig warning` widoczne na Archu nie są przyczyną crasha.
