# OuterClient v5.5

## Fix from the Fabric error screenshot

The screenshot showed:
- profile: Minecraft 1.16.5 + Fabric
- Java 8
- ImmediatelyFast build intended for Minecraft 26.2.x + Java 25

Java 8 is correct for Minecraft 1.16.5.
The installed ImmediatelyFast file was the incompatible component.

v5.5 reads `fabric.mod.json` directly from local JAR files.
Before launching a Fabric profile, obviously incompatible Minecraft-version mods
are moved to:

`<profile>/mods-disabled/`

They are never deleted.

Unknown/complex dependency syntax is left untouched rather than guessed.

## Fabric API

Every Fabric profile now automatically gets a Fabric API version filtered by:
- the profile Minecraft version
- Fabric loader

This happens:
- after creating a Fabric profile
- at startup for existing Fabric profiles
- before launching a Fabric profile

Existing Fabric API is not downloaded again.

## Java Manager

Settings → System tools now shows:
- Minecraft bundled runtime
- every detected system Java
- Java major version
- full executable path
- per-profile selected Java

Controls:
- automatic Minecraft runtime
- scan Java
- choose java.exe/java manually
- download/repair the Minecraft runtime
- select a specific Java for the active profile

When automatic mode is on, OuterClient prefers Minecraft's own runtime.
When it is off, the profile-specific Java path is passed explicitly.

## Microsoft login

Microsoft login uses the registered callback:

`http://localhost:8765/callback`

The OAuth URL:
- opens in the normal system browser
- stays visible inside the Microsoft Accounts page
- can be opened again
- can be copied manually

No separate OuterClient login window is used.

## Mod links / local mod information

Manage Profile reads `fabric.mod.json` locally, so mod name/version can appear
even before Modrinth metadata lookup succeeds.

Each mod gets a `Mod page` button:
- Modrinth project page when known
- Fabric metadata homepage/sources when available
- Modrinth search fallback otherwise

## Desktop shortcut icon

Windows shortcut now explicitly uses the packaged `outerclient.ico`.
Linux shortcut uses `outerclient-logo.png`.

The shortcut still points to OuterClient's stable managed location, so updates
replace the target without requiring a new shortcut.

## Profile icons

All existing profiles without a custom icon are filled with the OuterClient logo.
New profiles keep the same behavior.

## Build

GitHub Actions:
`Build and Release OuterClient 5.5`

Expected files:
- `OuterClient-v5.5-x86_64.AppImage`
- `OuterClient-v5.5.exe`
