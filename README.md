# OuterClient v4.8

## Profile manager przebudowany

Usunięto górne przyciski:
- Profiles
- Manage profile

Teraz każdy profil ma własny przycisk:
- Select
- Manage
- Delete

Kliknięcie **Manage** otwiera manager od razu dla tego konkretnego profilu.

W lewym górnym rogu managera jest:
`← Profiles`

Powrót prowadzi bezpośrednio do głównej listy profili.

## Zarządzanie zawartością profilu

Manager nadal pozwala usuwać:
- Mods
- Resource packs
- Shaders
- Datapacks

Dodałem również szybki przycisk do otwarcia folderu zarządzanego profilu.

## CurseForge Mods — opcjonalnie

v4.8 ma eksperymentalną integrację z CurseForge dla modów.

Wymagany jest własny **CurseForge API Key**:
`Settings → Advanced options → CURSEFORGE API KEY`

W ekranie zawartości można przełączyć źródło:
- Modrinth
- CurseForge

CurseForge w v4.8:
- wyszukuje mody dla wersji Minecrafta wybranego profilu,
- filtruje po Fabric / Forge / Quilt / NeoForge,
- pobiera pliki przez oficjalne API,
- instaluje wymagane zależności (`RequiredDependency`),
- sprawdza `allowModDistribution` oraz `isAvailable`,
- nie instaluje projektu, jeśli CurseForge blokuje dystrybucję.

CurseForge wymaga klucza API i nie wszystkie projekty pozwalają na dystrybucję przez zewnętrzne launchery.

## Arch Linux

```bash
cd OuterClient_v4_8
chmod +x install_linux.sh run_outerclient.sh
./install_linux.sh
./run_outerclient.sh
```
