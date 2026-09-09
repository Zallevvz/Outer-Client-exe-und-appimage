# OuterClient v5.4

## Minecraft launch
Launch flow rebuilt around minecraft-launcher-lib repair/install behavior.

Before launch:
- base Minecraft is verified/repaired,
- the Minecraft-provided Java runtime is installed with the game,
- the mod loader is found or installed,
- the local modded version is repaired where possible,
- the command uses the runtime declared by Minecraft instead of forcibly replacing it with a system Java.

## Microsoft
OAuth opens in the normal system browser from the Tk main thread.
Account management remains inside the main OuterClient window.

## Desktop shortcut + updates
Settings → System tools:
- Add / update desktop shortcut
- Remove shortcut

Managed target:
- Windows: `%LOCALAPPDATA%\OuterClient\OuterClient.exe`
- Linux: `~/.local/share/OuterClient/OuterClient.AppImage`

The shortcut points to this stable target. When OuterClient installs a newer release,
the target is replaced and the shortcut automatically starts the newest version.

## Profile icon
If no custom icon is selected, the OuterClient logo is saved as the profile icon.

## Mods / Modrinth
- Manage Profile reads mods directly from disk before online metadata lookup finishes.
- Search cards include an in-launcher Details page.
- Install + version arrow remains available.

## Build
Actions → Build and Release OuterClient 5.4

Assets:
- OuterClient-v5.4-x86_64.AppImage
- OuterClient-v5.4.exe
