# OuterClient v5.7

## Desktop shortcut icon

This fixes the icon of the **desktop shortcut itself**.

### Linux / KDE Plasma
OuterClient now:
- detects the localized desktop directory with `xdg-user-dir DESKTOP`,
- installs its icon into the user's `hicolor` icon theme,
- uses `Icon=outerclient` in the `.desktop` file,
- creates/updates the application entry in `~/.local/share/applications`,
- refreshes KDE / desktop icon caches when the required utilities are available.

This also supports Polish desktop folders such as `~/Pulpit`.

### Windows
The `.lnk` shortcut explicitly uses the packaged:
`outerclient.ico`

## CurseForge

CurseForge now supports the same main content tabs as Modrinth:
- Mods
- Resource packs
- Shaders
- Datapacks
- Modpacks

The search uses Minecraft CurseForge classes for each content type.

Every CurseForge result also has an `⌄` button next to Install.
It loads recent compatible CurseForge files and lets the user install a specific version.

### Installation destinations
- Mods → `mods/`
- Resource packs → `resourcepacks/`
- Shaders → `shaderpacks/`
- Datapacks → selected world's `datapacks/`
- Modpacks → create a new OuterClient profile

CurseForge modpacks parse `manifest.json`, create a profile using the pack's Minecraft
version and primary mod loader, download listed projects and apply the pack overrides.

## Build
GitHub Actions:
`Build and Release OuterClient 5.7`

Expected assets:
- `OuterClient-v5.7-x86_64.AppImage`
- `OuterClient-v5.7.exe`

The CurseForge key is still injected through the GitHub Actions secret:
`CURSEFORGE_API_KEY`
