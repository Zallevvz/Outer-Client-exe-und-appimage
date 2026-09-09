# OuterClient v5.3

## Minecraft 26.x / Java 25
Naprawiono ważny błąd Java Managera.

v5.2 traktował Minecraft 26.1.x jak starą numerację i wybierał Java 21.
Minecraft 26.1 wymaga Java 25.

v5.3:
- Minecraft 26.x → Java 25
- Minecraft 1.20.5–1.21.x → Java 21
- Minecraft 1.18–1.20.4 → Java 17
- starsze → Java 8

Przed instalacją/uruchomieniem OuterClient sprawdza właściwą Javę.
Jeśli jej brakuje, od razu pokazuje czytelny błąd zamiast wisieć na „Przygotowywanie gry”.

## Dolny pasek
Podczas uruchamiania Minecrafta pasek pobierania przełącza się w animowany tryb:
`Uruchamianie Minecrafta…`

Po uruchomieniu/niepowodzeniu wraca do normalnego paska pobierania.

## UI
Naprawiono obie duże puste przestrzenie:
- Ustawienia
- Zarządzaj profilem

Ustawienia są budowane od nowa w zwartym układzie:
- Ogólne
- Narzędzia systemowe

Manager profilu ma:
- nagłówek
- kategorie
- akcje
- listę modów

bez ważonego pustego wiersza pomiędzy elementami.

## Performance Pack
Performance Pack został usunięty z:
- tworzenia profilu,
- zarządzania profilem.

## Modpacki
Nowe profile z `.mrpack` zapisują również dokładną wersję loadera, jeśli manifest ją podaje.
OuterClient nadal próbuje pobrać ikonę projektu i ustawić ją jako ikonę profilu.

## Launch
- właściwa Java jest wybierana przed instalacją loadera,
- Java jest przekazywana także do instalatora modloadera,
- zapisywany jest dokładny loader version z modpacka,
- pełna komenda startowa trafia do logu,
- szybki crash pokazuje końcówkę `latest-minecraft.log`.

## GitHub
Actions → Build and Release OuterClient 5.3 → Run workflow

Pliki:
- OuterClient-v5.3-x86_64.AppImage
- OuterClient-v5.3.exe
