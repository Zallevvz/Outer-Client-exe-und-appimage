# OuterClient 7.3.1

OuterClient to niestandardowy launcher Minecrafta rozwijany dla Windows i Linux.

## Aktualna wersja

**7.3.1**

Najważniejsze zmiany w aktualnej linii 7.3.x:
- diagnostyka duplikatów modów z bezpieczną kopią zapasową i przywracaniem,
- szybszy selektor wersji Minecrafta z cache i odświeżaniem w tle,
- poprawki obsługi stanu uruchamiania Minecrafta,
- poprawki kart kont Microsoft,
- zachowanie wcześniejszych funkcji profili, Eksploruj, Biblioteki i diagnostyki.

## Uruchamianie źródła

Aktualny entrypoint wersji 7.3.1:

```bash
python outerclient_v731.py
```

`outerclient_v731.py` nakłada poprawki 7.3.0 i 7.3.1 na bazowy `outerclient.py`, dlatego moduły `outerclient_v730_*` są nadal potrzebne.

## Build

GitHub Actions:

**Build and Release OuterClient 7.3.1**

Workflow:

`.github/workflows/build-binaries-v731.yml`

Po ręcznym uruchomieniu workflow powstają:
- `OuterClient-v7.3.1-x86_64.AppImage`
- `OuterClient-v7.3.1.exe`

## Główne pliki

- `outerclient.py` — bazowy launcher,
- `outerclient_v730_*.py` — poprawki i funkcje 7.3.0 używane również przez 7.3.1,
- `outerclient_v731.py` — aktualny entrypoint,
- `outerclient_v731_patch.py` — hotfixy 7.3.1,
- `test_v730_core.py` i `test_outerclient_v731.py` — testy regresji,
- `assets/` — logo i ikony,
- `requirements.txt` — zależności Pythona.

Lokalne buildy, `__pycache__`, środowiska wirtualne i prywatny `outerclient_build_secrets.py` są ignorowane przez `.gitignore`.
