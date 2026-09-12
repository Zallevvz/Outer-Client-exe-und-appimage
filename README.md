# OuterClient 7.0

## Fixes and optimization
- What's New is persisted in `~/.outerclient-state.json` and opens automatically only once per release.
- Explore's profile picker is a true overlay and no longer shifts the page.
- The selected Explore target is hard-refreshed so icon/name/version/loader cannot remain blank.
- Profiles calculate Profile Health in a worker thread.
- Library uses a cheap filesystem signature, background indexing, cache and progressive rendering.
- Config writes are atomic and identical repeated writes are skipped.
- KDE Wayland uses one native managed title bar to avoid duplicate title bars while keeping taskbar/minimize behavior.
- X11 keeps the custom title bar and removes only native decoration through Motif hints.
- System Tools has a new taskbar/dock integration card with a stable app entry and icon.

## Build
GitHub Actions:
`Build and Release OuterClient 7.0`

Expected artifacts:
- `OuterClient-v7.0-x86_64.AppImage`
- `OuterClient-v7.0.exe`
