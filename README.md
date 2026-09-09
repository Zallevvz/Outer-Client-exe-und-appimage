# OuterClient v4.9.4

## Microsoft login fix

Naprawiono kilka rzeczy jednocześnie:

1. `CallbackHandler` nie wpisuje już na sztywno portu 8765.
   Używa dokładnego hosta i portu, na który wróciła przeglądarka.

2. OuterClient najpierw próbuje:
   `http://localhost:8765/callback`

3. Jeśli 8765 jest zajęty, automatycznie wybiera wolny port.

4. Timeout logowania zwiększono do 10 minut.

5. Na Linux/AppImage przeglądarka jest otwierana przez `xdg-open`
   z fallbackiem do `webbrowser.open`.

6. OuterClient zawsze pokazuje dodatkowe okno z pełnym linkiem OAuth:
   - Otwórz przeglądarkę
   - Kopiuj link

## Microsoft button

Kliknięcie `Microsoft` w Ustawieniach teraz naprawdę działa:

- jeśli konto jest zapisane → przełącza na Microsoft,
- jeśli konta nie ma → automatycznie otwiera manager i rozpoczyna logowanie.

## AppImage

Poprawka Pillow pozostaje w buildzie:

- `--collect-all PIL`
- `--hidden-import PIL.ImageTk`
- `--hidden-import PIL._tkinter_finder`

## GitHub

Zastąp:
- `outerclient.py`
- `.github/workflows/build-binaries.yml`

Następnie:
Actions → Build and Release OuterClient 4.9.4 → Run workflow

Pobierz:
- OuterClient-v4.9.4-x86_64.AppImage
- OuterClient-v4.9.4.exe
