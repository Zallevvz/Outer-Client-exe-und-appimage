# OuterClient v5.2

## Ustawienia
Ustawienia mają teraz dwie podzakładki:
- Ogólne
- Narzędzia systemowe

Java Manager i aktualizacje OuterClient nie zajmują już miejsca na stronie głównych ustawień.

## Profile i ikony
Każdy profil może mieć własną ikonę.

Ikonę można:
- wybrać podczas tworzenia profilu,
- zmienić w Edytuj profil,
- zmienić w Zarządzaj profilem,
- usunąć.

Ikona jest przechowywana w:
`<profil>/.outerclient/profile-icon.png`

Przy instalacji modpacka z Modrinth OuterClient automatycznie pobiera ikonę projektu
i ustawia ją jako ikonę nowo utworzonego profilu.

## Mody
Manager pokazuje pliki od razu.
Metadane Modrinth są skanowane automatycznie w tle.
Lista modów/resource packów/shaderów odświeża się sama, gdy zawartość folderu się zmieni.

## Graj
Dodano przycisk:
`Zakończ grę`

OuterClient nie przechodzi już zawsze przez pełne instalowanie profilu.
Jeśli zgodna wersja Minecrafta/loadera jest już zainstalowana, launcher używa jej od razu.

Status po zakończeniu Minecrafta wraca do `Gotowy / Ready`.

## Performance Pack
Pozostaje jeden rekomendowany Performance Pack Fabric.

## Modrinth
Pozostaje:
- szybsze ładowanie,
- poprawione ikony,
- `Install + ▼`,
- wybór konkretnej wersji moda.

## Build
GitHub:
Actions → Build and Release OuterClient 5.2 → Run workflow

Pliki:
- OuterClient-v5.2-x86_64.AppImage
- OuterClient-v5.2.exe
