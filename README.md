# OuterClient v5.5.2

## Hotfix

v5.5.1 contained a Python method-binding bug:

`_v55_version_tuple() takes 1 positional argument but 2 were given`

Cause:
`_v55_version_tuple` was attached to `OuterClient.simple_version_tuple`
but did not accept `self`.

v5.5.2 fixes the signature and includes a static validation pass for all
v5.x helper functions bound onto `OuterClient`, so the same class-binding
mistake is caught before packaging.

## Fabric API

The strict v5.5.1 compatibility logic remains enabled:
- exact Modrinth `game_versions` filtering,
- exact Fabric loader filtering,
- local `fabric.mod.json` verification,
- incompatible Fabric API moved to `mods-disabled`,
- never deleted.

## Build

GitHub Actions:
`Build and Release OuterClient 5.5.2`

Expected files:
- `OuterClient-v5.5.2-x86_64.AppImage`
- `OuterClient-v5.5.2.exe`
