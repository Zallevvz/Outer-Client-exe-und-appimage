# OuterClient v5.0

Duża aktualizacja interfejsu i funkcji.

## Nowy wybór profilu
Na ekranie Gra nie ma już małego dropdownu. Wybrany profil jest dużą kartą z nazwą, wersją Minecrafta, loaderem, presetem, RAM-em, Javą i liczbą modów. Profil można zmieniać strzałkami albo przez pełnoekranowy picker kart.

## Szybszy Modrinth
- wyniki po 24 zamiast 100+100,
- fuzzy fallback pobierany tylko gdy normalne wyszukiwanie ma mało wyników,
- cache wyszukiwań 5 minut,
- tylko 12 kart renderowanych naraz,
- Pokaż więcej ładuje kolejne 12,
- debounce wyszukiwania,
- tylko widoczne ikony są pobierane,
- Favorites.

## Profile
- Presety Low / Balanced / High / Custom,
- backup i restore,
- rozpoznawanie istniejących modów po SHA-1 przez Modrinth,
- sprawdzanie i instalowanie aktualizacji,
- Update all,
- Fabric Performance Pack: Sodium, Lithium, FerriteCore, ImmediatelyFast, Fabric API.

## Java Manager
Wykrywa Javy 8/17/21, określa wymaganą wersję dla Minecrafta i może automatycznie wybrać właściwą przy uruchomieniu.

## OuterClient updater
Może automatycznie sprawdzać Latest Release repozytorium GitHub i otworzyć stronę nowej wersji.

## Serwery
Nowa zakładka Serwery: adres + przypisany profil + Play.

## Diagnostyka
- latest-minecraft.log,
- OuterClient log,
- kopiowanie raportu,
- prosty crash detector (Java/RAM/mod conflict).

## Discord Rich Presence
Opcjonalne. W Opcjach zaawansowanych można podać własny Discord Application ID.

## Build
GitHub Actions buduje `OuterClient-v5.0-x86_64.AppImage` oraz `OuterClient-v5.0.exe`. Poprawka `PIL._tkinter_finder` pozostaje w workflow.
