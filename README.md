# OuterClient v5.10

## Custom popup windows

System message boxes have been replaced with OuterClient-styled dialogs.

Supported existing calls:
- showinfo
- showwarning
- showerror
- askyesno

The rest of OuterClient can keep calling `messagebox.*`; v5.10 redirects them
to the new custom dialog system.

Features:
- dark OuterClient styling
- rounded cards
- theme/accent border
- custom close button
- icon/state badge
- draggable custom title bar
- Enter to confirm
- Escape to close/cancel
- subtle fade-in animation
- dialogs centered over the launcher
- question dialogs return True/False exactly like askyesno

Worker-thread calls are dispatched back to the Tk main thread.

## Main window border

The main launcher keeps the normal Windows/Linux system title bar so resize,
maximize, taskbar integration and desktop-window management keep working.

OuterClient adds a polished inner window border:
- accent color while focused
- neutral border when unfocused

This avoids the reliability problems of completely frameless custom main
windows while still giving Windows and Linux a more consistent look.

## Build

GitHub Actions:
`Build and Release OuterClient 5.10`

Expected:
- `OuterClient-v5.10-x86_64.AppImage`
- `OuterClient-v5.10.exe`

CurseForge still uses:
`CURSEFORGE_API_KEY`
