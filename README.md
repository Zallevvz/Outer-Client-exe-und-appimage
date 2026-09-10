# OuterClient v5.10.3

## Fix for dark / flickering window

v5.10.2 remapped the root window every time Tk generated a `<Map>` event.
The remap itself generated another `<Map>` event, creating a loop:

withdraw -> overrideredirect -> deiconify -> Map -> repeat

Symptoms:
- dark/dim launcher
- flickering
- UI appearing frozen
- repeated remapping

v5.10.3 removes that loop.

Borderless/custom-titlebar mode is now:
- applied once after startup
- reapplied only after an actual minimize/restore transition
- guarded against re-entrant remaps

The custom title bar from v5.10.1 stays enabled:
- logo
- version
- minimize
- maximize/restore
- close
- window dragging
- edge/corner resizing

No native KDE/Windows title bar and no purple outer border.

## Build

GitHub Actions:
`Build and Release OuterClient 5.10.3`

Expected:
- `OuterClient-v5.10.3-x86_64.AppImage`
- `OuterClient-v5.10.3.exe`
