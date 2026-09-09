# OuterClient v4.9.2

## Microsoft login

Ta wersja nie używa stałego portu callback.

OuterClient binduje lokalny serwer do `127.0.0.1` z portem `0`,
więc system operacyjny wybiera wolny port automatycznie.

W razie błędu okno pokaże:
- `OuterClient 4.9.2`
- numer portu callback

Jeżeli okno programu nie pokazuje `4.9.2`, uruchomiony jest inny plik.

## GitHub

Workflow `.github/workflows/build.yml` buduje wyłącznie v4.9.2.

Po **Run workflow** automatycznie tworzy Release:
`OuterClient v4.9.2`

i ustawia go jako **Latest**.

Pliki do pobrania:
- `OuterClient-v4.9.2-x86_64.AppImage`
- `OuterClient-v4.9.2.exe`

Przed uruchomieniem workflow zastąp w repozytorium stare pliki zawartością tej paczki,
szczególnie `outerclient.py` oraz `.github/workflows/build.yml`.
