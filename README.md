# OuterClient v5.1

## Główne zmiany

### Microsoft
- Zarządzanie kontami działa wewnątrz głównego okna launchera.
- OAuth otwiera systemową przeglądarkę.
- Nie ma osobnego okna OuterClient do logowania.

### Profile
- `Zmień profil` otwiera pełną stronę z dużymi kartami profili.
- Tworzenie nowego profilu odbywa się wewnątrz launchera.
- Jest strzałka powrotu.
- Na ekranie Graj jest suwak RAM zapisujący RAM osobno dla profilu.

### Performance Pack
Jedna rekomendowana paczka Fabric:
- Sodium
- Lithium
- FerriteCore
- ImmediatelyFast
- EntityCulling
- Fabric API

Można ją:
- zaznaczyć podczas tworzenia profilu,
- zainstalować lub zainstalować ponownie w `Zarządzaj profilem`.

### Modrinth
- Pierwsze wyszukiwanie jest lżejsze.
- Na start renderowanych jest mniej kart.
- Ikony są tworzone po stronie głównego wątku Tk.
- Przycisk instalacji ma układ `Install + ▼`.
- `▼` pokazuje zgodne wersje projektu bez opuszczania strony.
- Można zainstalować konkretną wersję moda.

### Windows
Uruchamianie Minecrafta:
- dobiera Javę pod wersję profilu,
- ustawia `executablePath` i `defaultExecutablePath`,
- ustawia `JAVA_HOME`,
- loguje pełną komendę startową,
- jeśli Minecraft kończy się od razu, pokazuje ostatnie linie logu zamiast milczeć.

### Ustawienia
Java Manager i aktualizacje OuterClient są na samym dole przewijanej strony Ustawień.

## GitHub

Podmień:
- `outerclient.py`
- `.github/workflows/build-binaries.yml`

Uruchom:
`Actions → Build and Release OuterClient 5.1 → Run workflow`

Pliki:
- `OuterClient-v5.1-x86_64.AppImage`
- `OuterClient-v5.1.exe`
