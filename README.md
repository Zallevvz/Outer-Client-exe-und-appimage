# OuterClient 6.1

## What's New
- New permanent `Co nowego? / What's New` sidebar page.
- It opens automatically once on the first launch after each launcher update.
- The last seen version is stored as `whats_new_seen_version`.
- The page currently includes release notes for 6.1 and 6.0.

## Explore
- Sidebar `Modrinth` is now `Eksploruj` in Polish and `Explore` in English.
- The section still contains both Modrinth and CurseForge.
- `Install to profile` was rebuilt to always show profile icon, name,
  Minecraft version and loader.
- The selector opens inline and modpacks explicitly show `New profile`.

## Diagnostics
- Diagnostics has an independent profile selector in the upper-left.
- Results refresh for the chosen profile.
- Repair acts on the profile selected in Diagnostics.

## Linux taskbar/minimize
- The custom title bar is kept.
- On Linux/KDE OuterClient keeps the root as a normal managed window instead
  of leaving it override-redirect.
- Native decorations are removed through Motif hints where supported.
- This restores normal taskbar presence, Alt-Tab integration and minimization.

## Build
GitHub Actions:
`Build and Release OuterClient 6.1`

Expected:
- `OuterClient-v6.1-x86_64.AppImage`
- `OuterClient-v6.1.exe`

CurseForge:
`CURSEFORGE_API_KEY`
