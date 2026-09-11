# OuterClient 6.0

Major update focused on daily use and reliability.

## New Dashboard
- quick profile switching directly on the Play page
- profile icon, Minecraft version, loader and RAM
- local profile-health score
- play time, launch count and last-played stats
- cached mod-update count
- recommended RAM based on profile size
- quick links to repair, diagnostics and update checks

## Profile Health
OuterClient checks locally before you need to read a Fabric crash window:
- Minecraft / loader installation
- Java major version
- Fabric mod duplicates
- Fabric Minecraft-version constraints
- Fabric API presence

The checker is intentionally conservative: unknown dependency syntax is not treated as an error.

## Snapshots and rollback
Profile Manager now shows profile health and snapshot state.
Snapshots cover mutable content:
- mods
- resourcepacks
- shaderpacks
- config
- options.txt
- OuterClient content metadata

OuterClient automatically creates a snapshot before individual or bulk content updates.
The newest five snapshots are retained by default.

## Content Library
A new Library navigation page aggregates installed mods, resource packs, shaders and datapacks across every profile. It supports search and category filtering and links back to the relevant profile manager.

## Profiles
The Profiles page also shows a local health score for every profile and adds a one-click Play action without first returning to the dashboard.

## Diagnostics 2.0
Diagnostics now has status cards for:
- Minecraft / loader
- Java
- mods
- account
- Modrinth / CurseForge services

Logs remain available below the health overview.

## Local play statistics
OuterClient records locally per profile:
- successful launches
- play time
- last played time
- last Minecraft exit code

No telemetry is sent anywhere.

## Safer content updates
- automatic snapshot before updates
- corrected update-candidate filtering for Modrinth vs CurseForge metadata
- same existing rollback/full-backup tools remain available

## Build
GitHub Actions workflow: `Build and Release OuterClient 6.0`

Expected assets:
- `OuterClient-v6.0-x86_64.AppImage`
- `OuterClient-v6.0.exe`
