# OuterClient 7.4.0 — Motion & Polish

## Animacje i mikrointerakcje

- Płynna zmiana aktywnej pozycji w sidebarze.
- Delikatny reveal całych stron po wejściu.
- Kaskadowe pojawianie się kart.
- Hover glow i miękkie przejścia kolorów kart.
- Mikroanimacja wciśnięcia przycisków.
- Animowany focus glow pól tekstowych i textboxów.
- Płynna interpolacja globalnego paska pobierania.
- Slide-in / slide-out toastów.
- Fade + lekki slide okien dialogowych tam, gdzie wspiera to system.
- Pulsowanie kolorów dla aktywnych stanów ładowania.
- Staggered reveal wyników Modrinth.
- Animowane przyciski w selektorze wersji Minecrafta.
- Animowanie nowo otwieranych paneli wersji i wyboru profilu.

## Wydajność i bezpieczeństwo

- Brak `time.sleep()` w wątku UI.
- Wszystkie animacje działają przez `after()`.
- Tokeny anulują stare animacje tego samego widgetu.
- Limity liczby skanowanych i animowanych widgetów.
- Efekty są best-effort i nie blokują działania launchera po błędzie.
- `OUTERCLIENT_REDUCED_MOTION=1` wyłącza warstwę ruchu.

## Zachowane poprawki

7.4.0 nakłada się na 7.3.2, więc zachowuje m.in.:
- poprawki główek kont Microsoft oraz „Zmień skina” / „Zmień nick”,
- czyszczenie starego statusu uruchamiania Minecrafta,
- naprawę duplikatów modów,
- cache i szybszy selektor wersji,
- wcześniejsze poprawki Eksploruj i kolejki pobierania.
