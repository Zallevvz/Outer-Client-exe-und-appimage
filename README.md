# OuterClient v5.5.1

## Fabric API hotfix

v5.5 could incorrectly keep or install a Fabric API build for the wrong
Minecraft version.

Example from testing:
- profile Minecraft: 26.2
- wrong Fabric API: 0.116.17+1.21.1

v5.5.1 uses three safety layers:

1. Existing Fabric API JARs are read through `fabric.mod.json`.
2. Modrinth versions are fetched and then explicitly filtered by:
   - exact `game_versions` match
   - Fabric loader
3. The downloaded JAR is opened and its local Minecraft dependency is verified
   before it is accepted.

A definitely incompatible Fabric API is moved to:

`mods-disabled/`

It is never deleted.

The Fabric semantic-version parser also understands dependency range boundary
forms such as versions ending in `-`.

## Build

GitHub Actions:
`Build and Release OuterClient 5.5.1`

Expected files:
- `OuterClient-v5.5.1-x86_64.AppImage`
- `OuterClient-v5.5.1.exe`
