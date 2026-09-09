# OuterClient v4.9

## Microsoft Application jest wbudowane
OuterClient używa teraz zatwierdzonego Application (client) ID automatycznie.
Nie ma już pola Client ID do ręcznego wpisywania.

## Wiele kont Microsoft
Kliknij panel konta w lewym dolnym rogu, aby otworzyć manager kont.

Możesz:
- dodać kolejne konto Microsoft,
- zapisać kilka kont,
- przełączyć konto jednym kliknięciem,
- wylogować aktywne konto,
- usunąć zapisane nieaktywne konto,
- przełączyć się na Offline bez usuwania pozostałych kont.

Podczas dodawania nowego konta Microsoft launcher wymusza ekran wyboru konta,
co ułatwia dodanie drugiego lub trzeciego konta.

## Migracja ze starszych wersji
Jeżeli `~/.outerclient.json` zawiera stare pojedyncze pole `account`,
v4.9 automatycznie przenosi je do nowej listy kont.
Profile i pozostałe ustawienia nie wymagają usuwania.

## Odświeżanie sesji
Przed uruchomieniem Minecrafta OuterClient próbuje odświeżyć aktywną sesję
Microsoft przy użyciu zapisanego refresh tokenu.

## Ustawienia zaawansowane
Microsoft Client ID został usunięty z ustawień, ponieważ jest wbudowany.
CurseForge API Key nadal znajduje się w `Settings → Advanced options`.

## Arch Linux

```bash
cd OuterClient_v4_9
chmod +x install_linux.sh run_outerclient.sh
./install_linux.sh
./run_outerclient.sh
```
