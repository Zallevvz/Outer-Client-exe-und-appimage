# OuterClient v5.8

## Fixes from v5.7

### Desktop shortcut
v5.7 could fail with:

`name 'asset_path' is not defined`

v5.8 adds a real PyInstaller/AppImage-safe resource resolver.

Linux/KDE:
- detects the localized Desktop/Pulpit folder,
- installs `outerclient.png` into the user hicolor theme,
- the application menu entry uses `Icon=outerclient`,
- the desktop shortcut additionally uses an absolute PNG path,
- refreshes KDE/icon caches when available.

Windows:
- shortcut explicitly uses packaged `outerclient.ico`.

### Microsoft sign-in
The Microsoft page was successfully redirecting to:

`http://localhost:8765/callback?code=...`

but the browser received `ERR_CONNECTION_REFUSED`.

v5.8 runs callback listeners for both:
- `127.0.0.1:8765`
- `[::1]:8765` when IPv6 is available

The registered OAuth redirect remains exactly:
`http://localhost:8765/callback`

Both listeners stay alive with `serve_forever()` until the OAuth callback is received
or the 10 minute timeout expires.

### Update check
`Check now` always reports a result:
- update available → download/install prompt,
- current version → visible information dialog,
- GitHub/network failure → visible error dialog.

Release discovery uses `/releases?per_page=20` and chooses the newest stable version.

## Performance

### Faster OuterClient startup
Startup no longer:
- scans every Java installation immediately,
- checks/downloads Fabric API for every Fabric profile,
- rewrites/copies the AppImage shortcut target every launch.

Java detection is lazy and runs when System Tools is opened.
Automatic update checks are delayed until after the UI is already responsive.

### Faster Minecraft launch
Existing installed profiles use a fast local path:
- locate installed launch version,
- reuse the existing Minecraft runtime/system Java,
- locally verify Fabric compatibility only when the mods folder changed,
- reuse existing compatible Fabric API without a network query.

Full `install_minecraft_version()` verification/download is reserved for:
- first profile launch,
- missing launch version/runtime,
- repair situations.

## Build
GitHub Actions:
`Build and Release OuterClient 5.8`

Expected assets:
- `OuterClient-v5.8-x86_64.AppImage`
- `OuterClient-v5.8.exe`

CurseForge still uses the repository secret:
`CURSEFORGE_API_KEY`
