# OuterClient v5.10.2

## KDE / Linux title-bar hotfix

v5.10.1 could show two bars on KDE:
1. the native KDE title bar
2. the new OuterClient custom title bar

v5.10.2 fixes this by remapping the root window in borderless mode:
- withdraw
- overrideredirect(True)
- remove Tk highlight/border
- deiconify
- reapply after mapping

On X11/XWayland, OuterClient also tries a `_MOTIF_WM_HINTS`
fallback through `xprop` to remove KWin decorations.

The custom OuterClient bar remains:
- logo
- version
- minimize
- maximize/restore
- close
- dragging
- edge/corner resizing

No colored outer border is used.

## Build

GitHub Actions:
`Build and Release OuterClient 5.10.2`

Expected:
- `OuterClient-v5.10.2-x86_64.AppImage`
- `OuterClient-v5.10.2.exe`
