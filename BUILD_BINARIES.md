# Budowanie gotowych wersji OuterClient v4.9

## Najłatwiej: GitHub Actions

W paczce znajduje się:

`.github/workflows/build.yml`

Po wrzuceniu całej zawartości repozytorium na GitHub:

1. Otwórz repozytorium.
2. Wejdź w **Actions**.
3. Wybierz **Build OuterClient**.
4. Kliknij **Run workflow**.
5. Po zakończeniu pobierz dwa artifacts:

- `OuterClient-v4.9-Windows-x64`
- `OuterClient-v4.9-Linux-x86_64`

Pierwszy zawiera:

`OuterClient-v4.9.exe`

Drugi:

`OuterClient-v4.9-x86_64.AppImage`

## Automatyczny Release

Jeśli wypchniesz tag:

```bash
git tag v4.9
git push origin v4.9
```

workflow zbuduje obie wersje i doda je do GitHub Release.

## Budowanie lokalne

Linux:

```bash
chmod +x build_appimage.sh
./build_appimage.sh
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

## Microsoft

Microsoft Application ID jest już wbudowane w `outerclient.py`.
Użytkownik końcowy nie musi go wpisywać.
